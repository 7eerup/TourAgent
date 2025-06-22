## llm 답변 실제로 받아보자

# 1. State 정의 및 그래프 초기화
import os
from dotenv import load_dotenv, find_dotenv

# .env 파일에서 GOOGLE API 키를 불러와 환경변수에 설정
load_dotenv(find_dotenv())

os.environ["GOOGLE_API_KEY"] = os.getenv("LKK_GOOGLE_API_KEY")
os.environ['TAVILY_API_KEY'] = os.getenv("KYN_TAVILY_API")

import operator
import json
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from .teamdb_prompts_v6_kny import (combined_table_info,
                               tourinfo_table_info,
                               weather_table_info,
                               accommodation_table_info,
                               restaurant_table_info,
                               sql_generation_prompt,
                               tourinfo_query_prompt,
                               restaurant_query_prompt,
                               accommodation_query_prompt,
                               project_context,
                               select_place_prompt,
                               answer_prompt,
                               rewrite_question_prompt
                               )

class State(TypedDict):
    question:                    Annotated[str, "Question"] # 질문
    query:                       Annotated[str, "Query"] # SQL Query문
    query_accommodation:         Annotated[str, "Query_Accommodation"]
    query_restaurant:            Annotated[str, "Query_Restaurant"]
    query_tourinfo:              Annotated[str, "Query_TourInfo"]
    
    places:                      Annotated[list[str], "Selected_Places"] # 선택된 장소들
    web_results:                 Annotated[str, "Web_Results"] # 웹 검색 결과
    
    # query_web:                   Annotated[str, "Web_Query"] # 웹 검색용 쿼리
    # fetch_web:                   Annotated[str, "Web_Results"] # 웹 검색 결과
    
    fetch_db_accommodation:      Annotated[str, "Fetch_db_accommodation"]
    fetch_db_restaurant:         Annotated[str, "Fetch_db_restaurant"]
    fetch_db_tourinfo:           Annotated[str, "Fetch_db_tourinfo"]
    answer:                      Annotated[str, "Answer"] # 답변
    messages:                    Annotated[list, add_messages] # 메시지 (누적되는 list)
    relevance:                   Annotated[str, "Relevance"] # 관련성 여부
    # 병렬 처리 결과물 저장할 필드들 (reducer 사용)
    all_queries:                 Annotated[dict, operator.or_]
    all_results:                 Annotated[dict, operator.or_]

### LLM 정의
from langchain_google_genai                      import GoogleGenerativeAI
from langchain_core.prompts                      import PromptTemplate
from langchain.chains                            import create_sql_query_chain
from langchain.utilities                         import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_tavily                            import TavilySearch

import datetime

import ast

# DB 엔진 설정 (환경에 맞게 수정)
HOST                 = os.getenv("DB_HOST")
PORT                 = os.getenv("DB_PORT")
USERNAME             = os.getenv("DB_USER")
PASSWORD             = os.getenv("DB_PASSWORD")
DB_SCHEMA            = os.getenv("DB_NAME")

mysql_uri = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_SCHEMA}"


llm = GoogleGenerativeAI(model='gemini-2.0-flash')

## tavily 추가
tool = TavilySearch(
    max_results=3,
    topic="general"
)

# city = "서울"
# district = "성동구"
# theme = 'culture-experience'
# theme_to_category_two = {
#     'culture-experience':      '문화시설',
#     'historical-tour':         '역사관광지',
#     'urban-healing':           '휴양관광지',
#     'k-culture-experience':    '체험관광지',
#     'urban-forest-mountain-trail': '자연관광지',
#     'media-art-festival':      '공연/행사',
#     'feast-of-flavors-tour':   '맛코스',
# }
# category_two = theme_to_category_two[theme]

# 'culture-experience': '종합 예술,문화 공간 체험', -> 문화시설
# 'historical-tour': '역사 이야기 길 따라가기', -> 역사관광지
# 'urban-healing': '도심 속 안식처 속 힐링', -> 휴양관광지
# 'k-culture-experience': 'K-컬처 메이킹 체험', -> 체험관광지
# 'urban-forest-mountain-trail': '도시 속 힐링 숲, 산 둘레길', -> 자연관광지
# 'media-art-festival': '미디어 예술 축제,페스티벌', ->공연/행사, 축제
# 'feast-of-flavors-tour': '맛의 향연 투어(맛집 투어)', -> 맛코스

# travel_theme = "문화 체험"

# companions = "연인"
# group_size = 2
# meal_schedule = {"breakfast": 'True',
#                 "lunch": 'False',
#                 "dinner": 'True'}
# schedule = {"startDate": "2025-06-20",
#             "endDate": "2025-06-22"}

# Day 단위로 하기 때문에 Day 바뀌면 바뀌지, 한 Day안에서 바뀔 일은 없음 (챗으로 변수가 생기면 나중에 추가해서 구현해야 함)
# gu = '강남구' # SQL문 "강남구"를 포함해서 가져와
# how_long = '2박3일'
# travel_theme = '산여행'
# eat_number = '아침/점심/저녁' #아침, 점심, 저녁 중복 선택 가능 # 문자열 # 식당을 몇 개로 넣을지를 알아야 하기 때문
# 브레이크 타임, 영업시간 고려해서 뽑아와야 함

# with_who = '가족' #연인, 친구, 가족 # 문자열 -> # 물어보긴 하지만, LG에 넣지는 않음
# party_size = 4 #여행인원 수 # int # 물어보긴 하지만, LG에 넣지는 않음
# 1안) 위 2개는 top 20개를 뽑아서 llm한테 추천해달라고 하는 형식

## 2안) 네이버 블로그 api 이용해서 '가족'이면 '가족'이랑 명소명/식당/숙소 같이 넣어서 검색한 후에 결과를 받아서
##      LLM이 추천하는 형식

## 날씨 데이터를 명소 단위로 불러오지 말고, 구 단위로 불러오자 (설득이 필요함)
### 구단위로 25개씩 받아오는 방법

# location_preference = "popular" # "popluar":혼잡한지역 or "quiet":조용한지역 # 추가 데이터



# 현재 시점(YYYY-MM-DD HH:MM:SS) 저장

now_date = datetime.datetime.now().strftime("%Y-%m-%d")
now_time = datetime.datetime.now().strftime("%H:%M:%S")
now_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

db = SQLDatabase.from_uri(mysql_uri)

# SQL 실행 도구 정의
execute_query = QuerySQLDatabaseTool(db=db)

#################################################

# 2. 노드 정의
## def

def create_query_tourinfo(state: State) -> dict:
    
    question = state["question"]
    # 사용자의 요청에 맞는 쿼리 생성
    write_query = create_sql_query_chain(llm,
                                         db,
                                         tourinfo_query_prompt.partial(
                                             dialect=db.dialect,
                                             current_time=now_date_time,
                                             table_info=tourinfo_table_info,
                                             top_k=20,
                                             city=city,
                                             gu=district,
                                             category_two=category_two,
                                             companions=companions,
                                             group_size=group_size
                                             )
                                         )
    result = write_query.invoke({"question": question})
    print(result)
    clean_query = result.replace("```sql", "").replace("```", "").strip()
    print(clean_query)
    # return State(query_tourinfo=clean_query)
    return {"query_tourinfo": clean_query,
            "all_queries": {"tourinfo": clean_query}}

def create_query_accommodation(state: State) -> dict:
    
    question = state["question"]
    # 사용자의 요청에 맞는 쿼리 생성
    write_query = create_sql_query_chain(llm,
                                         db,
                                         accommodation_query_prompt.partial(
                                             dialect=db.dialect,
                                             current_time=now_date_time,
                                             table_info=accommodation_table_info,
                                             top_k=20,
                                             gu=district
                                             )
                                         )
    
    result = write_query.invoke({"question": question})
    print(result)
    clean_query = result.replace("```sql", "").replace("```", "").strip()
    print(clean_query)
    return {"query_accommodation": clean_query,
            "all_queries": {"accommodation": clean_query}}

def create_query_restaurant(state: State) -> dict:
    
    question = state["question"]
    # 사용자의 요청에 맞는 쿼리 생성
    write_query = create_sql_query_chain(llm,
                                         db,
                                         restaurant_query_prompt.partial(
                                             dialect=db.dialect,
                                             current_time=now_date_time,
                                             table_info=restaurant_table_info,
                                             top_k=20,
                                             gu=district
                                             )
                                         )
    
    result = write_query.invoke({"question": question})
    print(result)
    clean_query = result.replace("```sql", "").replace("```", "").strip()
    print(clean_query)
    return {"query_restaurant": clean_query,
            "all_queries": {"restaurant": clean_query}}


def fetch_db_tourinfo(state: State) -> dict:
    
    query = state["query_tourinfo"]
    
    fetch_db = execute_query.invoke({"query": query})
    print(fetch_db)
    # return State(fetch_db_tourinfo=fetch_db)
    return {"fetch_db_tourinfo": fetch_db,
            "all_results": {"tourinfo": fetch_db}}

def fetch_db_accommodation(state: State) -> dict:
    
    query = state["query_accommodation"]
    
    fetch_db = execute_query.invoke({"query": query})
    print(fetch_db)
    return {"fetch_db_accommodation": fetch_db,
            "all_results": {"accommodation": fetch_db}}

def fetch_db_restaurant(state: State) -> dict:
    
    query = state["query_restaurant"]
    
    fetch_db = execute_query.invoke({"query": query})
    print(fetch_db)
    return {"fetch_db_restaurant": fetch_db,
            "all_results": {"restaurant": fetch_db}}


# 사용자의 질문과 답변에 맞게 장소를 정함
def select_place(state: State) -> dict:
    # gemini 답변
    question = state["question"]
    
    # all_queries = state["all_queries"]
    all_results = state["all_results"]
    
    answer_chain = select_place_prompt.partial(
                                               city=city,
                                               district=district,
                                               category_two=category_two,
                                               companions=companions,
                                               group_size=group_size,
                                               breakfast=meal_schedule['breakfast'],
                                               lunch=meal_schedule['lunch'],
                                               dinner=meal_schedule['dinner'],
                                               startDate=schedule['startDate'],
                                               endDate=schedule['endDate']
                                               ) | llm | StrOutputParser()

    selected_place = answer_chain.invoke({
        "question": question,
        # "query_tourinfo": all_queries["tourinfo"],
        # "query_accommodation": all_queries["accommodation"],
        # "query_restaurant": all_queries["restaurant"],
        "fetch_db_tourinfo": all_results["tourinfo"],
        "fetch_db_accommodation": all_results["accommodation"],
        "fetch_db_restaurant": all_results["restaurant"]
    })
    
    print(selected_place)
    
    selected_place_list = ast.literal_eval(selected_place)
    
    print(selected_place)
    print(type(selected_place))
    print(selected_place_list)
    print(type(selected_place_list))
    
    return State(places=selected_place_list)

def search_web(state: State) -> dict:
    
    all_text = ""
    
    places = state['places']
    
    print(places)
    
    for place in places:

        print(place)
        
        if not place:
            continue
        
        all_text += f"{places} 웹 검색 결과: "
        print(district + " " + place)
        result = tool.invoke({"query": district + " " + place})
        print(result)
        for re in result['results']:
            all_text += '\n' + re['content']
        
        all_text += '\n'
    
    return {"web_results": all_text}

def generate_message(state: State) -> State:
    # gemini 답변
    question = state["question"]
    
    all_queries = state["all_queries"]
    all_results = state["all_results"]
    
    web_results = state["web_results"]
    
    answer_chain = answer_prompt.partial(project_context=project_context,
                                         city=city,
                                         district=district,
                                         category_two=category_two,
                                         companions=companions,
                                         group_size=group_size,
                                         breakfast=meal_schedule['breakfast'],
                                         lunch=meal_schedule['lunch'],
                                         dinner=meal_schedule['dinner'],
                                         startDate=schedule['startDate'],
                                         endDate=schedule['endDate'],
                                         web_results=web_results
                                         ) | llm | StrOutputParser()

    print(all_queries["tourinfo"])
    print(all_queries["accommodation"])
    print(all_queries["restaurant"])
    print(all_results["tourinfo"])
    print(all_results["accommodation"])
    print(all_results["restaurant"])

    
    answer = answer_chain.invoke({
        "question": question,
        "query_tourinfo": all_queries["tourinfo"],
        "query_accommodation": all_queries["accommodation"],
        "query_restaurant": all_queries["restaurant"],
        "fetch_db_tourinfo": all_results["tourinfo"],
        "fetch_db_accommodation": all_results["accommodation"],
        "fetch_db_restaurant": all_results["restaurant"],
        # "web_results": web_results,
    })
    
    return State(answer=answer)

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

# 3. 그래프 정의 및 엣지 연결

# Langgraph.graph에서 StateGraph와 END를 가져옵니다.
graph = StateGraph(State)

# 노드 추가

graph.add_node("create_query_tourinfo", create_query_tourinfo)
graph.add_node("create_query_accommodation", create_query_accommodation)
graph.add_node("create_query_restaurant", create_query_restaurant)
graph.add_node("fetch_tourinfo", fetch_db_tourinfo)
graph.add_node("fetch_accommodation", fetch_db_accommodation)
graph.add_node("fetch_restaurant", fetch_db_restaurant)

graph.add_node("select_place", select_place)
graph.add_node("search_web", search_web)

graph.add_node("generate_message", generate_message)

# 엣지로 노드 연결

graph.add_edge(START         , "create_query_tourinfo")
graph.add_edge(START         , "create_query_accommodation")
graph.add_edge(START         , "create_query_restaurant")
graph.add_edge("create_query_tourinfo", "fetch_tourinfo")
graph.add_edge("create_query_accommodation", "fetch_accommodation")
graph.add_edge("create_query_restaurant", "fetch_restaurant")

graph.add_edge(["fetch_tourinfo", "fetch_accommodation", "fetch_restaurant"], "select_place")

graph.add_edge("select_place", "search_web")

graph.add_edge("search_web", "generate_message")

graph.add_edge("generate_message", END)

# 기록을 위한 메모리 저장소 생성
memory = MemorySaver()

# 그래프 컴파일
app = graph.compile(checkpointer=memory)

from IPython.display import Image, display

# 그래프 시각화
display(Image(app.get_graph().draw_mermaid_png()))

from langchain_core.runnables import RunnableConfig

config = RunnableConfig(recursion_limit=30,
                        configurable={"thread_id": "1"})


# {
#   "session_parameters": {
#     "city": "서울",
#     "district": "서초구",
#     "theme": "해변 산책",
#     "startDate": "2025-08-01",
#     "endDate": "2025-08-03",
#     "companions": "동료",
#     "groupSize": 4,
#     "mealSchedule": ["아침", "점심", "저녁"]
#   }
# }

def get_result(session_parameters: dict) -> str:
    global city, district, theme, category_two, startDate, endDate, companions, groupSize, group_size, meal, meal_schedule, schedule
    city = session_parameters.get("city")
    district = session_parameters.get("district")
    if not district:
        raise ValueError("'district' 파라미터가 필요합니다.")
    theme = session_parameters.get("theme")
    theme_to_category_two = {
        '종합 예술,문화 공간 체험':      '문화시설',
        '역사 이야기 길 따라가기':         '역사관광지',
        '도심 속 안식처 속 힐링':           '휴양관광지',
        'K-컬처 메이킹 체험':    '체험관광지',
        '도시 속 힐링 숲, 산 둘레길': '자연관광지',
        '미디어 예술 축제,페스티벌':      '공연/행사',
        '맛의 향연 투어(맛집 투어)':   '맛코스',
        }
    category_two = theme_to_category_two[theme]
    startDate = session_parameters.get("startDate")
    endDate = session_parameters.get("endDate")
    companions = session_parameters.get("companions")
    groupSize = session_parameters.get("groupSize")
    group_size = groupSize
    meal = session_parameters.get("mealSchedule")
    
    meal_schedule = {
        'breakfast': 'True' if '아침' in meal else 'False',
        'lunch':     'True' if '점심' in meal else 'False',
        'dinner':    'True' if '저녁' in meal else 'False',
        }
    
    schedule = {"startDate": startDate,
                "endDate": endDate}
    
    """
    Args:
        session_parameters (dict): {"city": "...", "district": "...", ...}

    Returns:
        str: LLM이 생성한 answer 문자열
    """

    # LangGraph 실행
    response = app.invoke({"question": district}, config=config)
    results = response['answer'].replace("```json","").replace("```","")
    js_result = json.loads(results)
    js_result_answer = js_result['answer']
    print("answer res: " , js_result_answer )
    js_result_places = js_result['places']
    print("place res: " , js_result_places )
    return js_result_answer, js_result_places