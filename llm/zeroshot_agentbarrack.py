# import os
# import dotenv
# import openai

# dotenv.load_dotenv()
# openai.api_key = os.getenv('OPENAI_API_KEY')

from typing import List

import presets

from operator import itemgetter

from langchain.agents import AgentExecutor, create_tool_calling_agent

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from typing import Callable, List, Sequence, Tuple

from langchain_core.agents import AgentAction
from langchain_core.messages import BaseMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from langchain.agents.format_scratchpad.tools import (
    format_to_tool_messages,
)
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser

MessageFormatter = Callable[[Sequence[Tuple[AgentAction, str]]], List[BaseMessage]]


class ZeroShotAgentBarrack():
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
            preset = presets.PRESET_ZS_DEFAULT
        self.preset = preset
        
        print('Use the presets provided by ZeroShotAgentBarrack: ', self.preset['preset_name'])

        if verbose is None:
            verbose = False
        self.verbose =verbose

        if 'gpt' in self.preset['model_id']:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=self.preset['model_id'], 
                temperature=0,
                openai_api_key=self.preset['openai_api_key'],
                )
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

        self.memory = None
        if self.preset['memory'] == True:
            self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.preset['template']),
                    ('placeholder', "{chat_history}"),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )
        else:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.preset['template']),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )

    def make_tool_from_ClosestFinder(
            self,
            preset,
            ONLINE=False,
            ):
        from langchain.agents import Tool
        
        name = preset['tool_preset_name']       # 툴 이름
        target_places = preset['target_places'] # 근처 가까운 타겟 장소를 조회할 좌표 리스트
        if not ONLINE:
            location_coordinates = preset['location_coordinates']   # 유저의 현재 위치를 조회할 좌표 리스트
            proofreading_list = preset['proofreading']              # 입력지역 오타 단어 교정 리스트

        def recommend_closest_place_offline(current_location):
            from geopy.distance import geodesic
            from difflib import get_close_matches

            def sido_replace(sentence):
                import re
                replacements_space = {
                "서울 ": "서울특별시 ",
                "서울시 ": "서울특별시 ",
                "부산 ": "부산광역시 ",
                "부산시 ": "부산광역시 ",
                "대구 ": "대구광역시 ",
                "대구시 ": "대구광역시 ",
                "인천 ": "인천광역시 ",
                "인천시 ": "인천광역시 ",
                "광주 ": "광주광역시 ",
                "광주시 ": "광주광역시 ",
                "대전 ": "대전광역시 ",
                "대전시 ": "대전광역시 ",
                "울산 ": "울산광역시 ",
                "울산시 ": "울산광역시 ",
                "세종 ": "세종특별자치시 ",
                "세종시 ": "세종특별자치시 ",
                "경기 ": "경기도 ",
                "충북 ": "충청북도 ",
                "충남 ": "충청남도 ",
                "전남 ": "전라남도 ",
                "경북 ": "경상북도 ",
                "경남 ": "경상남도 ",
                "강원 ": "강원특별자치도 ",
                "강원도 ": "강원특별자치도 ",
                "전북 ": "전북특별자치도 ",
                "전라북도 ": "전북특별자치도 ",
                "제주 ": "제주특별자치도 ",
                "제주도 ": "제주특별자치도 ",
                }

                pattern = re.compile("|".join(re.escape(key) for key in replacements_space.keys()))

                def replace_match(match):
                    return replacements_space[match.group(0)]

                return pattern.sub(replace_match, sentence)
            
            administrative_district = get_close_matches(current_location, proofreading_list, n=1)[0]
            administrative_district = sido_replace(administrative_district)
            
            for location in location_coordinates.keys():
                if administrative_district in location:
                    corrected_location = location
            print('Proceed offline.')
            print('The address has been adjusted: ' + corrected_location)

            user_location_coordinates = location_coordinates[corrected_location]
            location_with_distance = [
                (name, geodesic(user_location_coordinates, coords).km)
                for name, coords in target_places.items()
            ]
            location_with_distance.sort(key=lambda x: x[1])
            closest_places = location_with_distance[:3]

            result = ', '.join(place[0] for place in closest_places)
            return result
        
        def recommend_closest_place_online(current_location):
            from geopy.distance import geodesic
            import googlemaps
            print('Proceed online.')
            print('Use Google Maps.')
            maps = googlemaps.Client(key='AIzaSyDmhs0v_3Bkuk6zuonr3rJwZrZlGPuvbtY')
            geo_location = maps.geocode(current_location)[0].get('geometry')
            user_location_coordinates = (geo_location['location']['lat'], geo_location['location']['lng'])
            print(f"User Location Coordinates: {user_location_coordinates}")
            location_with_distance = []
            for name, coords in target_places.items():
                distance = geodesic(user_location_coordinates, coords).km
                location_with_distance.append((name, distance))
                # print(f"Distance to {name}: {distance:.2f} km")

            location_with_distance.sort(key=lambda x: x[1])
            closest_places = location_with_distance[:3]
            print('closest_places: ' + str(closest_places))

            result = ', '.join(place[0] for place in closest_places)
            return result

        recommend_closest_place_tool = Tool(
            name=name,
            func=recommend_closest_place_online if ONLINE else recommend_closest_place_offline,
            description=(
                "현재 위치에서 가장 가까운 곳을 알려주는 도구입니다."
                "정확한 형식으로 호출하세요: recommend_closest_place(current_location: str)"
                "예: '인천 서구에서 가장 가까운 곳.'의 경우 recommend_closest_place('인천 서구') "
                )
                )
        
        self.tools.append(recommend_closest_place_tool)
        

    def make_agent(
            self,
            message_formatter: MessageFormatter = format_to_tool_messages,
            ):
        
        if self.preset['memory'] == True:
            self.agent = (
                RunnablePassthrough.assign(
                    agent_scratchpad=lambda x: message_formatter(x["intermediate_steps"]),
                    chat_history=RunnableLambda(self.memory.load_memory_variables)
                    | itemgetter(self.memory.memory_key)
                )
                | self.prompt
                | self.llm.bind_tools(self.tools)
                | ToolsAgentOutputParser()
            )
        else:
            self.agent = create_tool_calling_agent(
                self.llm, 
                self.tools, 
                self.prompt,
                )
        
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=3,
        )

    def invoke_agent(self, input):
        self.input = input
        self.result = self.executor.invoke({"input": self.input})
        self.output = self.result['output']

        if self.preset['memory'] == True:
            self.memory.save_context(inputs={"human": self.input}, outputs={"ai": self.output})

        return self.output