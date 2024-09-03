import os
import dotenv

import openai
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class AgentBarrack():
    def __init__(self,
                 model_id = 'gpt-4-turbo',
                 prompt = '당신은 매우 친절한 챗봇 도우미입니다. 문장의 주어에 주의하며 대답합니다.',
                 tools = []
                 ):
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        self.tools = tools

        self.chat_history = []
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
        self.agent = None
        self.agent_executor = None
        self.input = ''

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
        
    def make_tool_from_DocRetriever(self, dir_path, name: str, description: str, extension='txt', embedding=OpenAIEmbeddings()):
        from langchain_community.document_loaders import DirectoryLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain.tools.retriever import create_retriever_tool

        loader = DirectoryLoader(path=dir_path, glob='*.'+extension, show_progress=True)
        data = loader.load()
        # print(data)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        splits = text_splitter.split_documents(data)

        # print(splits)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="similarity")
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            )
        self.tools.append(retriever_tool)

    def make_tool_from_CsvRetriever(self, dir_path, name: str, description: str, embedding=OpenAIEmbeddings()):
        import pandas as pd
        from langchain_community.document_loaders.dataframe import DataFrameLoader
        from langchain_community.vectorstores import FAISS
        from langchain.tools.retriever import create_retriever_tool

        # csv파일 path로 변경해야함.
        df = pd.read_csv("./images/gov_faq_data.csv", index_col=0)
        df['combined_content'] = "질문: " + df['question'] + " 답변: " + df['answer']

        # category, question, answer, links 삭제하고, combined_content만 유지
        df = df.drop(columns=['category','question', 'answer', 'links'])

        loader = DataFrameLoader(
            data_frame=df,
            page_content_column="combined_content"
            )
        data = loader.load()
        # print(data)

        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        splits = text_splitter.split_documents(data)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        print(splits)

        # vectorstore = FAISS.from_documents(documents=data, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="similarity")
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            )
        self.tools.append(retriever_tool)

    def make_tool_from_JsonlRetriever(self, jsonl_path, name: str, description: str, embedding=OpenAIEmbeddings()):
        from langchain_community.document_loaders import JSONLoader
        from langchain_community.vectorstores import FAISS
        from langchain.tools.retriever import create_retriever_tool

        def metadata_func(record: dict, metadata: dict) -> dict:
            metadata["question"] = record.get("question")
            metadata["answer"] = record.get("answer")
            return metadata

        loader = JSONLoader(
            file_path=jsonl_path, 
            jq_schema='.', 
            json_lines=True,
            text_content=False,
            content_key="content",
            metadata_func=metadata_func, 
            )
        data = loader.load()
        vectorstore = FAISS.from_documents(documents=data, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="similarity")
        retriever_tool = create_retriever_tool(
            retriever,
            name=name,
            description=description,
            )
        self.tools.append(retriever_tool)

    # def make_tool_from_KGChain(self,
    #                            source_text,
    #                            name='',
    #                            description='마이크로 서비스, 종속성 또는 할당된 것에 대한 질문에 답해야 할 때 유용합니다. 작업 수 계산 등과 같은 모든 종류의 집계에도 유용합니다.',
    #                            model_name='gpt-4-turbo',
    #                            NEO4J_URI=os.getenv('NEO4J_URI'), 
    #                            NEO4J_USERNAME=os.getenv('NEO4J_USERNAME'), 
    #                            NEO4J_PASSWORD=os.getenv('NEO4J_PASSWORD')):
        
    #     from langchain_experimental.graph_transformers import LLMGraphTransformer
    #     from langchain_core.documents import Document
    #     from langchain_community.graphs import Neo4jGraph
    #     from langchain.chains import GraphCypherQAChain
    #     from langchain.agents import Tool

    #     llm_transformer = LLMGraphTransformer(llm=ChatOpenAI(temperature=0, model_name=model_name))

    #     documents = [Document(page_content=source_text)]
    #     graph_documents = llm_transformer.convert_to_graph_documents(documents)

    #     knowledge_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    #     knowledge_graph.add_graph_documents(graph_documents)

    #     cypher_chain = GraphCypherQAChain.from_llm(
    #         cypher_llm = ChatOpenAI(temperature=0, model_name=model_name),
    #         qa_llm = ChatOpenAI(temperature=0),
    #         graph=knowledge_graph,
    #         verbose=True)
        
    #     self.tools.append(
    #         Tool(
    #             name=name,
    #             func=cypher_chain.invoke,
    #             description=description
    #         ))

    #     return graph_documents
        
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
        
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
    
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