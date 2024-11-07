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

        self.prompt = PromptTemplate.from_template(self.preset['template'])
        self.memory = None
        if self.preset['memory'] == True:
            self.memory = ConversationBufferMemory(return_messages=False, memory_key="chat_history")

        self.agent = None
        self.executor = None

        self.input = ''
        self.output = ''

    def make_tool_from_Function(
            self,
            name,
            func,
            description,
            ):
        from langchain.agents import Tool

        function_tool = Tool(
            name=name,
            func=func,
            description=description,
        )
        self.tools.append(function_tool)

    def make_tool_from_ClosestFinder(
            self,
            preset,
            ):
        
        def recommend_closest_place_online(current_location):
            from geopy.distance import geodesic
            import googlemaps
            maps = googlemaps.Client(key=presets.API_KYES['google_maps_api_key'])
            print('User Location: ', current_location)

            geo_results = maps.geocode(current_location)
            retry_count = 0
            while not geo_results and retry_count < 1:
                time.sleep(1)
                geo_results = maps.geocode(current_location)
                retry_count += 1

            if geo_results:
                geo_location = maps.geocode(current_location)[0].get('geometry')
                user_location_coordinates = (geo_location['location']['lat'], geo_location['location']['lng'])
                print(f"User Location Coordinates: {user_location_coordinates}")
            else:
                print('The closest one was not found.')
                return '가까운 곳을 찾지 못 하였습니다.'
            
            location_with_distance = []
            for name, coords in preset['target_places'].items():
                distance = geodesic(user_location_coordinates, coords).km
                location_with_distance.append((name, distance))
                # print(f"Distance to {name}: {distance:.2f} km")
            location_with_distance.sort(key=lambda x: x[1])
            closest_places = location_with_distance[:3]
            print('closest_places: ' + str(closest_places))

            result = ', '.join(place[0] for place in closest_places)
            return result
        
        print('Proceed with the provided preset: ', preset['preset_name'])

        from langchain.agents import Tool
        recommend_closest_place_tool = Tool(
            name=preset['tool_preset_name'],
            func=recommend_closest_place_online,
            description=preset['description'],
            )
        
        self.tools.append(recommend_closest_place_tool)

    def make_tool_from_DocRetriever(
            self, 
            doc_path : str, 
            name: str, 
            description: str,
            chunk_size=470,
            chunk_overlap=45,
            model_name='text-embedding-3-large',
            ):

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
            embeddings = OpenAIEmbeddings(
                model=model_name,
                openai_api_key=self.preset['openai_api_key'],
                )
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
        self.result = ''

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
        
    def invoke_agent(self, input, MAX_REPETITIONS=2):
        # 특정 단어들이 문장 안에 있을 경우 그 문장을 삭제
        def remove_error_sentences(text, n=3):
            keywords = ['죄송', 'sorry', 'format', '포맷', '오류', 'error']
            sentences = re.findall(r'([^.,!?]+[.,!?]?)', text)
            check_limit = min(len(sentences), max(2, n))
            
            filtered_sentences = [
                sentence for i, sentence in enumerate(sentences)
                if i >= check_limit or not any(keyword in sentence for keyword in keywords)
            ]
            
            result = ''.join(filtered_sentences).strip()
            if result and not result.endswith(('.', '?', '!', '~')):
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
            lines = text.splitlines()
            for line in lines:
                if not re.fullmatch(r'^[a-zA-Z0-9\s.,?!\'\"()-]*$', line):
                    return False
            return True

        self.input = input
        repetition_count = 0
        while repetition_count < (MAX_REPETITIONS + 1):
            start_time = time.time()
            result = self.executor.invoke({"input": self.input})
            self.result = result

            if contains_keywords(result.get('output')):
                intermediate_steps = result.get('intermediate_steps', [])
                log_list = []
                log_len = []
                for step in intermediate_steps:
                    log = step[0].log
                    if ('Action Input: ' in log) or ('Question: ' in log) or is_all_english(log):
                        continue
                    log = remove_all_english_sentences(log)
                    log = remove_error_sentences(log)
                    log_list.append(log)
                    log_len.append(len(log))
                
                if len(log_len) == 0:
                    output = ''
                else:
                    max_len_index = log_len.index(max(log_len))
                    output = log_list[max_len_index]
            else:
                output = result.get('output')

            if not output.replace(' ', '').replace('\n', '') or is_all_english(output):
                end_time = time.time()
                print(
                    f'repetition_count: {repetition_count} / {MAX_REPETITIONS}',
                    '\tElapsed time: {:.2f}'.format(end_time - start_time)
                    )
                repetition_count += 1
                print('Repeat again because all sentences are NULL or English.')
            else:
                end_time = time.time()
                print(
                    f'repetition_count: {repetition_count} / {MAX_REPETITIONS}',
                    '\tElapsed time: {:.2f}'.format(end_time - start_time)
                    )
                break

        self.output = output.replace('Thought: ', '').replace('; ', '. ')

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
    print('2024.11.07.16:00')