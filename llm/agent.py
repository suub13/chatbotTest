from langchain.agents import BaseSingleActionAgent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class CustomAgent(BaseSingleActionAgent):
    def __init__(self, llm_chain, tools):
        self.llm_chain = llm_chain
        self.tools = tools
        self.chat_history = []  # 대화 기록을 저장할 리스트

    def plan(self, intermediate_steps, **kwargs):
        # 대화 기록(chat_history)과 중간 결과(agent_scratchpad)를 kwargs에 포함
        return self.llm_chain.run(**kwargs)  # LLM 체인 실행

    def update_chat_history(self, user_input, agent_output):
        # 대화 기록을 업데이트하는 메서드
        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": agent_output})

# MyAgent 클래스 수정
class MyAgent:
    def __init__(self, model_id='gpt-4-turbo', prompt='당신은 매우 친절한 챗봇 도우미입니다.', tools=[]):
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        self.tools = tools

        # ChatPromptTemplate 설정
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # LLMChain 생성
        self.prompt_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

        # CustomAgent 생성
        self.agent = CustomAgent(self.prompt_chain, self.tools)

        # AgentExecutor 설정
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)

    def get_response(self, user_input):
        # 사용자 입력을 받아서 응답 생성
        agent_output = self.agent_executor.run({"input": user_input, "chat_history": self.agent.chat_history})
        
        # 대화 기록 업데이트
        self.agent.update_chat_history(user_input, agent_output)
        
        return agent_output
