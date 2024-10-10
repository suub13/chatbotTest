
# 요약
PRESET_A = {
    'preset_name': 'PRESET_A',
    'max_iterations': 10,
    'max_execution_time': 20,
    'template': """
    Answer the following questions as best you can.
    You must answer in a narrative, one-line format.
    All answers should be in Korean.
    You have access to the following tools:
    {tools}

    Previous conversation:
    {chat_history}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """,
}

# 장문
PRESET_B = {
    'preset_name': 'PRESET_B',
    'max_iterations': 8,
    'max_execution_time': 15,
    'template': """
    Answer the following questions as best you can.
    You must also provide a link to the supporting legislation.
    All answers should be in Korean.
    You have access to the following tools:
    {tools}

    Previous conversation:
    {chat_history}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """
}

# 요약 질문
PRESET_C = {
    'preset_name': 'PRESET_C',
    'max_iterations': 10,
    'max_execution_time': 20,
    'template': """
    Answer the following questions as best you can.
    You must answer in a narrative, one-line format.
    You must ask one or two questions to check if there is any missing information or considerations.
    You need to understand the situation the human is in from previous conversations.
    All answers should be in Korean.
    You have access to the following tools:
    {tools}

    Previous conversation:
    {chat_history}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """,
}