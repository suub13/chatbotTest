import llm.agentbarrack

agent = llm.agentbarrack.AgentBarrack(prompt='당신은 매우 친절한 민원 처리 상담사입니다. 숫자와 점이외의 특수문자는 사용하지 않고 대답해야 하며 컨텍스트에서 답을 추론할 수 없는 경우 대답하지 마세요.',
                                  model_id='gpt-4-turbo'
                                  )
agent.make_tool_from_DocRetriever(dir_path='./assets',
                                  name='solution-tools',
                                  description='민원에 대한 해결방안을 제시해야할 때 유용합니다.',
                                  )
agent.make_agent()


print(agent.invoke_agent('취학통지서를 온라인에서 발급받으려면 세대주만 받을 수 있는거야?'))
print(agent.invoke_agent('내가 취학통지서를 신청했는데 그 인쇄가능 기간동안 인쇄를 안했으면 어떻게 해?'))
print(agent.invoke_agent('문서 프린트하기 눌렀는데 가로로 잘려, 이거 안짤리는 방법이 있어?'))
