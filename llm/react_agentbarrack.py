import os
import dotenv
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

import time
from typing import List, Optional, Union

from operator import itemgetter

from langchain import PromptTemplate

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain_core.tools.render import ToolsRenderer, render_text_description
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

from langchain.agents import AgentOutputParser, AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser


class ReActAgentBarrack():
    def __init__(
            self,
            model_id='gpt-4o',
            template='',
            tools=None,
            verbose=True,
            presets=None,
            ):
        if tools is None:
            tools = []
        if presets is None:
            print("No presets are provided, so we proceed with the defaults or input values.")
        else:
            template = presets['template']
            print('Proceed with the provided preset: ', presets['preset_name'])
        
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        self.tools = tools
        self.template = template
        self.prompt = PromptTemplate.from_template(self.template)
        self.presets = presets

        self.memory = ConversationBufferMemory(return_messages=False, memory_key="chat_history")
        self.agent = None
        self.executor = None
        self.verbose = verbose

        self.input = ''
        self.output = ''

        

    def make_tool_from_DocRetriever(
            self, 
            doc_path, 
            name: str, 
            description: str,
            chunk_size=700,
            chunk_overlap=70,
            embedding=OpenAIEmbeddings()):

        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain.tools.retriever import create_retriever_tool

        data = TextLoader(doc_path, encoding='utf-8').load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splits = text_splitter.split_documents(data)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="similarity")
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            )
        self.tools.append(retriever_tool)

    def make_agent(
            self,
            max_iterations: Optional[int] = 15,
            max_execution_time: Optional[float] = None,
            output_parser: Optional[AgentOutputParser] = None,
            tools_renderer: ToolsRenderer = render_text_description,
            stop_sequence: Union[bool, List[str]] = True,
            ):
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

        if self.presets is not None:
            max_iterations = self.presets['max_iterations']
            max_execution_time = self.presets['max_execution_time']

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools, 
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
            return_intermediate_steps=True,
            verbose=self.verbose, 
            )

    def invoke_agent(self, input):
        self.input = input
        
        output = 'Thought'
        repetition_count = 0
        while 'Thought' in output:
            start_time = time.time()
            print('repetition_count: ', repetition_count,
                  '\tStart time: ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))

            result = self.executor.invoke({"input": self.input})

            if result.get('output') == 'Agent stopped due to iteration limit or time limit.':
                intermediate_steps = result.get('intermediate_steps', [])
                if intermediate_steps:
                    last_step_2 = intermediate_steps[-2]
                    output_2 = last_step_2[0].log
                    
                    last_step_1 = intermediate_steps[-1]
                    output_1 = last_step_1[0].log

                    if len(output_2) > len(output_1):
                        output = output_2
                    else:
                        output = output_1
                    
                else:
                    output = 'Thought'
            else:
                output = result.get('output')
            
            end_time = time.time()
            print('repetition_count: ', repetition_count,
                  '\tStart time: ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
                  '\tElapsed time: {:.2f}'.format(end_time - start_time))

            repetition_count += 1

        self.output = output
        self.memory.save_context(inputs={"human": self.input}, outputs={"ai": self.output})

        return self.output

if __name__ == '__main__':
    print('class ReAct-Agent Barrack')
    print('2024.09.25.14:38')