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
        # 특정 단어들이 문장 안에 있을 경우 그 문장을 삭제
        def remove_error_sentences(text, n=3):
            keywords = ['죄송합니다', 'sorry', 'format', '포맷', '오류', 'error']
            sentences = text.split('. ')
            # 검사할 문장 수를 결정: 전체 문장이 n개 미만이면 2개까지만 검사
            check_limit = min(len(sentences), max(2, n))
            filtered_sentences = [
                sentence for i, sentence in enumerate(sentences) 
                if i >= check_limit or not any(keyword in sentence for keyword in keywords)
            ]
            result = '. '.join(filtered_sentences)
            if result and not result.endswith('.'):
                result += '.'
            return result
        
        # 영어문장이 있을 경우 그 문장을 삭제
        def remove_all_english_sentences(text):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            filtered_sentences = [
                sentence for sentence in sentences
                if not re.match(r'^[\sA-Za-z0-9,.\'\"!?;:\-_()@#&]+$', sentence.strip())
            ]
            return ' '.join(filtered_sentences).strip()
        
        # 특정 단어들이 문장 안에 있을 경우 True를 리턴
        def contains_keywords(text):
            keywords = ['time limit', 'assist']
            return any(keyword in text for keyword in keywords)
        
        # 모든 문장들이 영어일 경우 True를 리턴
        def is_all_english(text):
            sentences = text.split('. ')
            for sentence in sentences:
                if not re.match(r'^[a-zA-Z\s.,?!\'\"-]*$', sentence):
                    return False
            return True

        self.input = input
        
        output = 'Thought'
        repetition_count = 0
        while 'Thought' in output:
            start_time = time.time()
            print('repetition_count: ', repetition_count,
                  '\tStart time: ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))

            result = self.executor.invoke({"input": self.input})
            self.result = result

            if is_all_english(result.get('output')):
                continue
            
            if contains_keywords(result.get('output')):
                intermediate_steps = result.get('intermediate_steps', [])
                if intermediate_steps:
                    log_list = []
                    log_len = []
                    for step in intermediate_steps:
                        log = step[0].log
                        if 'Action Input: ' in log:
                            continue
                        log_list.append(log)
                        log_len.append(len(log))
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

        print(output)
        output = remove_error_sentences(output)
        output = remove_all_english_sentences(output)

        self.output = output

        if self.preset['memory'] == True:
            self.memory.save_context(inputs={"human": self.input}, outputs={"ai": self.output})

        return self.output
    

    def get_chat_history(self, ):
        if self.preset['memory'] == True:
            return self.memory.load_memory_variables({})["chat_history"]
        else:
            return self.memory
        
    def print_result_info(self):
        print(f"input:\n{self.result['input']}\n")
        print(f"output:\n{self.result['output']}\n")
        print('intermediate_steps:')
        for idx, step in enumerate(reversed((self.result['intermediate_steps']))):
            print(f'step {idx}: {step[0].log}')

if __name__ == '__main__':
    print('class ReAct-Agent Barrack')
    print('2024.10.29.13:48')