from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
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

def State():
    pass
def rewrite_user_question():
    pass
def fetch_db():
    pass
def create_query():
    pass
def relevance_check():
    pass
def generate_message():
    pass

decision = ""











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










clean_query = ""
execute_query = ""
answer = ""
def itemgetter() :
    pass









# ---------------------------------------------------------------
# 전체 파이프라인 체인 구성
# ---------------------------------------------------------------
chain = (
    RunnablePassthrough
      .assign(query=clean_query)
      .assign(result=itemgetter("query") | execute_query)
    | answer
)