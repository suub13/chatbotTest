import os
import dotenv

import openai
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# 내가 추가한 내용
from langchain.chains import LLMChain

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


'''
agent.make_tool_from_DocRetriever(
    doc_path='./assets/qna.txt',
    name='qna-relevant_statutory_provisions-tool',
    description='민원 질문에 대한 해결방법과 근거법령을 제시해야할 때 유용합니다.',
    )
    
agent.make_tool_from_DocRetriever(
    doc_path='/Users/nyagu/Documents/workSpace/PoC/assets/link.txt',
    name='statute_links-tool',
    description='근거법령의 link를 제시해야할 때 유용합니다.',
    )
'''

class AgentBarrack():
    def __init__(self,
                 model_id = 'gpt-4-turbo',
                 prompt = '당신은 매우 친절한 챗봇 도우미입니다. 문장의 주어에 주의하며 대답합니다.',
                 tools = []
                 ):
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        self.tools = tools

        self.chat_history = []
        # self.prompt -> self.prompt_template으로 변경
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
        # 내가 추가한 내용
        self.prompt_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

        self.make_tool_from_DocRetriever(
            doc_path='./assets/qna.txt',
            name='qna-relevant_statutory_provisions-tool',
            description='민원 질문에 대한 해결방법과 근거법령을 제시해야할 때 유용합니다.',
            )

        self.make_tool_from_DocRetriever(
            doc_path='./assets/link.txt',
            name='statute_links-tool',
            description='근거법령의 link를 제시해야할 때 유용합니다.',
            )


        self.agent = self.prompt_chain.bind_tools(self.tools)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)
        self.input = ''
        self.retriever_tool = None

    def make_tools_from_functions(self, functions: list, names: list, descriptions: list):
        from langchain.tools import StructuredTool

        for func, name, desc in zip(functions, names, descriptions):
            self.tools.append(
                StructuredTool.from_function(
                func=func,
                name=name,
                description=desc,
                )
            )
        
    def make_tool_from_DocRetriever(
            self, 
            doc_path, 
            name: str, 
            description: str,
            chunk_size=300,
            chunk_overlap=20,
            embedding=OpenAIEmbeddings()):

        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain.tools.retriever import create_retriever_tool

        data = TextLoader(doc_path).load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        splits = text_splitter.split_documents(data)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="similarity")
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            # return_direct=True,
            # verbose=True,
            )
        self.tools.append(retriever_tool)


    def make_agent(self):
        ### 반드시 tools가 선행되어 있어야함 ###
        self.agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                    x["intermediate_steps"]
                ),
                "chat_history": lambda x: x["chat_history"],
            }
            | self.prompt
            | self.llm.bind_tools(self.tools)
            | OpenAIToolsAgentOutputParser()
            )
        
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)
    
    def invoke_agent(self, input):
        self.input = input
        result = self.agent_executor.invoke({"input": input, "chat_history": self.chat_history})
        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=result["output"]),
        ])
        return result['output']


if __name__ == '__main__':

    print('class AgentBarraack')