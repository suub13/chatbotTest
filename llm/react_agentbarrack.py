import os
import dotenv
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

import time
import re
from typing import List, Optional, Union

import llm.presets as presets

from operator import itemgetter

from langchain import PromptTemplate

from langchain_core.tools.render import ToolsRenderer, render_text_description
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

from langchain.agents import AgentOutputParser, AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser


class ReActAgentBarrack():
    def __init__(
            self,
            tools=None,
            preset=None,
            verbose=None,
            ):
        
        if tools is None:
            tools = []
        self.tools = tools

        if preset is None:
            preset = presets.PRESET_DEFAULT
        self.preset = preset
        print('Proceed with the provided preset: ', self.preset['preset_name'])

        if verbose is None:
            verbose = False
        self.verbose =verbose

        if 'gpt' in self.preset['model_id']:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model=self.preset['model_id'], temperature=0)
        else:
            """
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

            llm = HuggingFaceEndpoint(
                repo_id="HuggingFaceH4/zephyr-7b-beta",
                task="text-generation",
                max_new_tokens=512,
                do_sample=False,
                repetition_penalty=1.03,
            )
            chat_model = ChatHuggingFace(llm=llm)
            """
            pass

        self.prompt = PromptTemplate.from_template(self.preset['template'])
        self.memory = None
        if self.preset['memory'] == True:
            self.memory = ConversationBufferMemory(return_messages=False, memory_key="chat_history")

        self.agent = None
        self.executor = None

        self.input = ''
        self.output = ''

    def make_tool_from_DocRetriever(
            self, 
            doc_path : str, 
            name: str, 
            description: str,
            chunk_size=470,
            chunk_overlap=45,
            model_name='text-embedding-3-large'):

        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_community.vectorstores.utils import DistanceStrategy
        from langchain.tools.retriever import create_retriever_tool

        data = TextLoader(doc_path, encoding='utf-8').load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splits = text_splitter.split_documents(data)

        if 'text-embedding' in model_name:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(model=model_name)
        else:
            """
            from langchain_huggingface.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            """
            pass
        
        vectorstore = FAISS.from_documents(documents=splits, 
                                           embedding=embeddings,
                                           distance_strategy = DistanceStrategy.COSINE,
                                           )
        
        retriever = vectorstore.as_retriever()
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            )
        self.tools.append(retriever_tool)

    def make_agent(
            self,
            output_parser: Optional[AgentOutputParser] = None,
            tools_renderer: ToolsRenderer = render_text_description,
            stop_sequence: Union[bool, List[str]] = True,
            ):
        
        if self.preset['memory'] == True:
            missing_vars = {"tools", "tool_names", "agent_scratchpad"}.difference(
                self.prompt.input_variables + list(self.prompt.partial_variables)
            )
            if missing_vars:
                raise ValueError(f"Prompt missing required variables: {missing_vars}")

            prompt = self.prompt.partial(
                tools=tools_renderer(list(self.tools)),
                tool_names=", ".join([t.name for t in self.tools]),
            )
            if stop_sequence:
                stop = ["\nObservation"] if stop_sequence is True else stop_sequence
                llm_with_stop = self.llm.bind(stop=stop)
            else:
                llm_with_stop = self.llm
            output_parser = output_parser or ReActSingleInputOutputParser()
            
            self.agent = (
                RunnablePassthrough.assign(
                    agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"]),
                    chat_history=RunnableLambda(self.memory.load_memory_variables)
                    | itemgetter(self.memory.memory_key)
                )
                | prompt
                | llm_with_stop
                | output_parser
            )
        else:
            self.agent = create_react_agent(
                    llm=self.llm,
                    tools=self.tools,
                    prompt=self.prompt,
                    )
            
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools, 
            handle_parsing_errors=True,
            max_iterations=self.preset['max_iterations'],
            max_execution_time=self.preset['max_execution_time'],
            return_intermediate_steps=True,
            verbose=self.verbose, 
            )

    def invoke_agent(self, input):

        def remove_first_error_sentence(text):
            sentences = text.split('.')
            first_sentence = sentences[0].strip()
            
            if "오류" in first_sentence or "error" in first_sentence:
                sentences = sentences[1:]
            result = '. '.join(sentences).strip()
            
            return result
        
        def remove_first_english_sentence(text):
            sentences = text.split('\n', 1)
            first_sentence = sentences[0].strip()

            if re.match(r'^[A-Za-z\s,.\'\"!?]+$', first_sentence):
                return sentences[1].strip() if len(sentences) > 1 else ""
            else:
                return text

        self.input = input
        
        output = 'Thought'
        repetition_count = 0
        while 'Thought' in output:
            start_time = time.time()
            print('repetition_count: ', repetition_count,
                  '\tStart time: ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))

            result = self.executor.invoke({"input": self.input})

            if (result.get('output') == 'Agent stopped due to iteration limit or time limit.') or ('assist' in result.get('output')):
                intermediate_steps = result.get('intermediate_steps', [])
                if intermediate_steps:
                    log_list = []
                    log_len = []
                    for step in intermediate_steps:
                        log_list.append(step[0].log)
                        log_len.append(len(step[0].log))
                    max_len_index = log_len.index(max(log_len))
                    output = log_list[max_len_index]
                else:
                    output = 'Thought'
            else:
                output = result.get('output')
            
            end_time = time.time()
            print('repetition_count: ', repetition_count,
                  '\tStart time: ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
                  '\tElapsed time: {:.2f}'.format(end_time - start_time))

            repetition_count += 1

        output = remove_first_error_sentence(output)
        output = remove_first_english_sentence(output)

        self.output = output

        if self.preset['memory'] == True:
            self.memory.save_context(inputs={"human": self.input}, outputs={"ai": self.output})

        return self.output
    

    def get_chat_history(self, ):
        if self.preset['memory'] == True:
            return self.memory.load_memory_variables({})["chat_history"]
        else:
            return self.memory

if __name__ == '__main__':
    print('class ReAct-Agent Barrack')
    print('2024.10.17.14:30')