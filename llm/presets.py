import ast
import os

def parse_file_to_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    try:
        result = ast.literal_eval(content)
        return result
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing file: {e}")
        return None

def read_list_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read().strip()
    return ast.literal_eval(data)


API_KYES = {
    'google_maps_api_key': os.getenv('google_maps_api_key')
}

PRESET_DEFAULT = {
    'preset_name': 'PRESET_DEFAULT',
    'model_id': 'gpt-4o',
    'openai_api_key': os.getenv('openai_api_key_default'),
    'max_iterations': 10,
    'max_execution_time': 20,
    'memory': False,
    'template': """
    Answer the following questions as best you can.
    All answers should be in Korean. but, if the address is in English, it will answer in English.

    You have access to the following tools:
    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    All answers should be in Korean. but, if the address is in English, it will answer in English.
    Begin!

    Question: {input}
    Thought:{agent_scratchpad}
    """,
}


# 요약
PRESET_A = {
    'preset_name': 'PRESET_A',
    'model_id': 'gpt-4o',
    'openai_api_key': os.getenv('openai_api_key_a'),
    'max_iterations': 8,
    'max_execution_time': 10,
    'memory': True,
    'template': """
    Answer the following questions as best you can.

    You are a counselor regarding a lost passport and you need to answer simply and clearly.
    You must only answer the question and not provide any additional information.
    Answer the question by inferring whether the questioner is domestic or international.
    If your location is in-country, you shouldn't mention a consulate or embassy.
    All answers should be in Korean. but, if the address is in English, it will answer in English.

    You have access to the following tools:
    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    All answers should be in Korean. but, if the address is in English, it will answer in English.
    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """,
}

# 장문
PRESET_B = {
    'preset_name': 'PRESET_B',
    'model_id': 'gpt-4o',
    'openai_api_key': os.getenv('openai_api_key_b'),
    'max_iterations': 8,
    'max_execution_time': 10,
    'memory': True,
    'template': """
    Answer the following questions as best you can.

    You are a counselor regarding a lost passport.
    You need to answer as much information as possible in a long-winded manner.
    If your location is in-country, you shouldn't mention a consulate or embassy.
    All answers should be in Korean. but, if the address is in English, it will answer in English.
    
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

    All answers should be in Korean. but, if the address is in English, it will answer in English.
    Begin!
    
    Question: {input}
    Thought: {agent_scratchpad}
    """
}

# 요약 질문
PRESET_C = {
    'preset_name': 'PRESET_C',
    'model_id': 'gpt-4o',
    'openai_api_key': os.getenv('openai_api_key_c'),
    'max_iterations': 8,
    'max_execution_time': 12,
    'memory': True,
    'template': """
    Answer the following questions as best you can.

    You are an active agent for lost passports and your answers should be simple and clear.
    Infer the information you think the questioner might want or need, and be sure to ask for it at the end of your answer.

    Answer the question by inferring whether the questioner is domestic or international.
    If your location is in-country, you shouldn't mention a consulate or embassy.
    All answers should be in Korean. but, if the address is in English, it will answer in English.

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

    If your location is in-country, you shouldn't mention a consulate or embassy.
    All answers should be in Korean. but, if the address is in English, it will answer in English.
    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """,
}


PRESET_ZS_DEFAULT = {
    'preset_name': 'PRESET_ZS_DEFAULT',
    'model_id': 'gpt-4o',
    'openai_api_key': os.getenv('openai_api_key_zs_default'),
    'memory': False,
    'template': "You are a helpful assistant. Respond only in korean.",
}

TOOL_PRESET_JUNKYARD = {
    'preset_name': 'TOOL_PRESET_JUNKYARD',
    'tool_preset_name': 'find_closet_junkyard-tool',
    'description': '현재 위치에서 가장 가까운 폐차장을 알려주는 도구입니다. 정확한 형식으로 호출하세요: recommend_closest_place(current_location: str) 예: "인천 서구에서 가장 가까운 곳."의 경우 recommend_closest_place("인천 서구")',
    'location_coordinates': parse_file_to_dict('./assets/geographic_coordinatesasd.txt'),
    'target_places': parse_file_to_dict('./assets/junkyard_coordinatesasd.txt'),
    'proofreading': read_list_from_txt('./assets/administrative_district_list.txt'),
    'TOP': 3,
}

TOOL_PRESET_DIPLOMATIC = {
    'preset_name': 'TOOL_PRESET_DIPLOMATIC',
    'tool_preset_name': 'find_closet_diplomatic-tool',
    'description': '국내(한국) 이외의 곳에 있을 경우, 현재 위치에서 가장 가까운 영사관 또는 대사관을 알려주는 도구입니다. 정확한 형식으로 호출하세요: recommend_closest_place(current_location: str) 예: "가마쿠라시에서 가장 가까운 곳."의 경우 recommend_closest_place("가마쿠라시")',
    'target_places': parse_file_to_dict('./assets/diplomatic_coordinatesasd.txt'),
    'TOP': 3,
}