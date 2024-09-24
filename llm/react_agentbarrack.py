import os
import dotenv
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from typing import List, Optional, Sequence, Union

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.tools import BaseTool
from langchain_core.tools.render import ToolsRenderer, render_text_description

from langchain import hub, PromptTemplate
from langchain.agents import AgentOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents import create_react_agent, AgentExecutor


class ReActAgentBarrack():
    def __init__(
            self,
            model_id='gpt-4o',
            # extra_details=' 그리고 한국어로 대답해야하고 근거법령이 있다면 그것에 대한 링크도 반드시 알려줘.',
            extra_details=' 그리고 근거법령이 있다면 그것에 대한 링크도 반드시 알려줘.',
            tools=[],
            ):
        
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        self.tools = tools
        # self.prompt = PromptTemplate(
        #     input_variables=hub.pull("hwchase17/react").input_variables,
        #     template=hub.pull("hwchase17/react").template + extra_details*3,
        # )
        # self.prompt = hub.pull("hwchase17/react")
        self.prompt = PromptTemplate(
            input_variables=["agent_scratchpad", "input", "tool_names", "tools"],
            template='''
            다음 질문에 최선을 다해 한국어로 답변하세요. 당신은 다음 도구들을 사용할 수 있습니다:

            {tools}

            다음 형식을 사용하세요:

            질문: 당신이 답변해야 할 입력 질문
            생각: 무엇을 해야 할지 항상 생각하세요
            행동: 취할 행동을 선택하세요 [{tool_names}] 중 하나
            행동 입력: 행동에 대한 입력값
            관찰: 행동의 결과
            ... (이 생각/행동/행동 입력/관찰이 N번 반복될 수 있습니다)
            생각: 이제 최종 답을 알았습니다
            최종 답변: 원래 질문에 대한 최종 답변
            
            시작하세요!

            질문: {input}
            생각: {agent_scratchpad}
            '''
        )
        self.extra_details = extra_details

        self.chat_history = []
        self.agent = None
        self.executor = None

        self.input = ''
        self.output = ''

        

    def make_tool_from_DocRetriever(
            self, 
            doc_path, 
            name: str, 
            description: str,
            chunk_size=470,
            chunk_overlap=35,
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
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | llm_with_stop
            | output_parser
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools, 
            handle_parsing_errors=True,
            max_iterations=5,
            max_execution_time=10,
            return_intermediate_steps=True,
            verbose=True, 
            )

    def _invoke_agent0(self, input):
        self.input = input
        result = self.executor.invoke({"input": input, "chat_history": self.chat_history})
        if result.get('output') == 'Agent stopped due to iteration limit or time limit.':
            intermediate_steps = result.get('intermediate_steps', [])
            if intermediate_steps:
                last_step_2 = intermediate_steps[-2]
                output_2 = last_step_2[0].log
                
                last_step_1 = intermediate_steps[-1]
                output_1 = last_step_1[0].log

                if len(output_2) > len(output_1):
                    self.output = output_2
                else:
                    self.output = output_1
                
            else:
                self.output = 'ERROR_00'
        else:
            self.output = result.get('output')
            print("에이전트 출력:", self.output)

        self.chat_history.extend([
            HumanMessage(content=self.input),
            AIMessage(content=self.output),
        ])

        return self.output

    def _invoke_agent1(self, input):
        self.input = input
        full_input = input + self.extra_details
        result = self.executor.invoke({"input": full_input, "chat_history": self.chat_history})
        return result

    def invoke_agent(self, input):
        self.input = input
        full_input = input + self.extra_details
        result = self.executor.invoke({"input": full_input, "chat_history": self.chat_history})

        if result.get('output') == 'Agent stopped due to iteration limit or time limit.':
            intermediate_steps = result.get('intermediate_steps', [])
            if intermediate_steps:
                last_step_2 = intermediate_steps[-2]
                output_2 = last_step_2[0].log
                
                last_step_1 = intermediate_steps[-1]
                output_1 = last_step_1[0].log

                if len(output_2) > len(output_1):
                    self.output = output_2
                else:
                    self.output = output_1
                
            else:
                self.output = 'ERROR_00'
        else:
            self.output = result.get('output')
            print("에이전트 출력:", self.output)

        self.chat_history.extend([
            HumanMessage(content=self.input),
            AIMessage(content=self.output),
        ])

        return self.output

if __name__ == '__main__':
    print('class ReAct-Agent Barrack')
    print('2024.09.23.15.48')