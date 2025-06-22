## llm 답변 실제로 받아보자

# 1. State 정의 및 그래프 초기화

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from personaldb_prompts import (combined_table_info,
                                sql_generation_prompt,
                                project_context,
                                answer_prompt,
                                rewrite_question_prompt
                                )


class State(TypedDict):
    question: Annotated[str, "Question"] # 질문
    query: Annotated[str, "Query"] # SQL Query문
    answer: Annotated[str, "Answer"] # 답변
    messages: Annotated[list, add_messages] # 메시지 (누적되는 list)
    relevance: Annotated[str, "Relevance"] # 관련성 여부
    

### LLM 정의
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_sql_query_chain
from langchain.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from dotenv import load_dotenv, find_dotenv
import datetime

import os

# .env 파일에서 GOOGLE API 키를 불러와 환경변수에 설정
load_dotenv(find_dotenv())

# DB 엔진 설정 (환경에 맞게 수정)
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DB_SCHEMA = os.getenv("DB_NAME")
# LIVESEOUL_TABLE_NAME = os.getenv("LIVESEOUL_TABLE_NAME")

mysql_uri = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_SCHEMA}"

os.environ["GOOGLE_API_KEY"] = os.getenv("LKK_GOOGLE_API_KEY")

llm = GoogleGenerativeAI(model='gemini-2.0-flash')

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

## 사용자의 요청을 재작성 (수정해야 함!!)

def rewrite_user_question(state: State):
    
    question = state["question"]
    
    rewrite_question_chain = rewrite_question_prompt.partial(table_info=combined_table_info,                                                        
                                                            current_date=now_date,
                                                            current_time=now_time
                                                            ) | llm | StrOutputParser()
    
    # 사용자의 요청을 좀 더 명확하게 변경함
    rewritten_question = rewrite_question_chain.invoke({
        "question": question
    })
    
    return State(question=rewritten_question)

def create_query(state: State) -> State:
    
    question = state["question"]
    # 사용자의 요청에 맞는 쿼리 생성
    write_query = create_sql_query_chain(llm,
                                         db,
                                         sql_generation_prompt.partial(
                                             dialect=db.dialect,
                                             current_time=now_date_time,
                                             table_info=combined_table_info
                                             )
                                         )
    
    result = write_query.invoke({"question": question})
    
    clean_query = result.replace("```sql", "").replace("```", "").strip()
    
    return State(query=clean_query)

def fetch_db(state: State) -> State:
    
    query = state["query"]
    
    fetch_db = execute_query.invoke({"query": query})
    
    return State(answer=fetch_db)

relevance_check_prompt = PromptTemplate.from_template(
    """
당신은 SQL 관련성 평가 전문가입니다.
아래 세 가지를 기준으로 사용자 질문과 생성된 SQL, 그리고 그 실행 결과가 사용자의 의도에 맞는지 **엄격하게** 평가하세요.

평가 기준:
- SQLQuery 문법이 옳고, 테이블·컬럼 이름이 스키마와 일치하는가?
- WHERE/JOIN 조건이 질문 의도(날짜·시간, 지역, 필터 등)에 부합하는가?
- SQLResult가 논리적으로 합당한 데이터(비어 있지 않고, 기대 범위의 값)인가?

**동작 방식**:
1. 만약 모든 평가 기준을 충족하면, `yes` 만 출력하세요.
2. SQLQuery 단계에 문제가 있다면, `SQLQuery` 만 출력하세요.
3. 결과(SQLResult) 단계에 문제가 있다면, `SQLResult` 만 출력하세요.

-- [Few-Shot Examples]  
Example 1:  
Question: “어제 서울 강수확률 알려줘.”  
SQLQuery: `SELECT * FROM Weather WHERE FCST_DATE = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AND AREA_NM = '서울';`  
SQLResult: `POP: 20`  
→ 평가: `yes`

Example 2:  
Question: “서울 영등포구 내일 최고기온”  
SQLQuery: `SELECT MAX(TMP) FROM Weather WHERE FCST_DATE = '2025-06-16';`  
SQLResult: `TMP: 30`  
→ 평가: `query`  _(지역 조건 `AREA_NM = '영등포구'`가 빠졌습니다.)_

Example 3:  
Question: “부산 오늘 최저기온”  
SQLQuery: `SELECT MIN(TMP) FROM Weather WHERE FCST_DATE = CURRENT_DATE() AND AREA_NM = '부산';`  
SQLResult: `TMP: NULL`  
→ 평가: `result`  _(결과가 비어 있어 실행 결과에 문제가 있습니다.)_

Question: {question}
SQLQuery: {query}
SQLResult: {result}
Answer:
"""
)


def relevance_check(state: State) -> State:
    
    question = state["question"] # 사용자가 입력한 question
    query = state["query"] # 작성한 sql query문
    result = state["answer"] # db에서 가져온 데이터
        
    relevance_check_chain = relevance_check_prompt | llm | StrOutputParser()
    
    is_relevant = relevance_check_chain.invoke({
        "question": question,
        "query": query,
        "result": result
    })
    
    return State(relevance=is_relevant)


def generate_message(state: State) -> State:
    # gemini 답변
    question = state["question"]
    query = state["query"]
    result = state["answer"]
    
    answer_chain = answer_prompt.partial(project_context=project_context) | llm | StrOutputParser()
    
    answer = answer_chain.invoke({
        "question": question,
        "query": query,
        "result": result
    })
    
    return State(answer=answer)
    
def decision(state: State) -> State:
    
    # 로직 추가 가능
    if state["relevance"] == "yes":
        return "yes"
    if state["relevance"] == "SQLQuery":
        return "SQLQuery"
    else:
        return "SQLResult"

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

# 3. 그래프 정의 및 엣지 연결

# Langgraph.graph에서 StateGraph와 END를 가져옵니다.
graph = StateGraph(State)

# 노드 추가
graph.add_node("rewrite_user_question", rewrite_user_question)
graph.add_node("create_query", create_query)
graph.add_node("fetch_db", fetch_db)
graph.add_node("relevance_check", relevance_check)
graph.add_node("generate_message", generate_message)

# 엣지로 노드 연결
graph.add_edge(START, "rewrite_user_question")
graph.add_edge("rewrite_user_question", "create_query")
graph.add_edge("create_query", "fetch_db")
graph.add_edge("fetch_db", "relevance_check")

# 조건부 엣지를 추가
graph.add_conditional_edges(
    "relevance_check", # 관련성 체크 노드에서 나온 결과를 is_relevant 함수에 전달
    decision,
    {
        "yes": "generate_message", # 관련성 있으면 llm에게 전달
        "SQLQuery": "create_query", # 관련성 체크 결과에서 더 안좋은 곳으로 가서, 다시 답변 생성
        "SQLResult": "fetch_db", # 관련성 체크 결과에서 더 안좋은 곳으로 가서, 다시 답변 생성
    }
)

graph.add_edge("generate_message", END)

# 기록을 위한 메모리 저장소 생성
memory = MemorySaver()

# 그래프 컴파일
app = graph.compile(checkpointer=memory)

from IPython.display import Image, display

# 그래프 시각화
png_path = './graph.png'
app.get_graph().draw_mermaid_png(output_file_path=png_path)
# display(Image(app.get_graph().draw_mermaid_png()))

from langchain_core.runnables import RunnableConfig

config = RunnableConfig(recursion_limit=10,
                        configurable={"thread_id": "1"})
89
# 외부에서 Graph와 State 타입, Config를 가져갈 수 있도록
__all__ = [
    "app",
    "State",
    "RunnableConfig"
]