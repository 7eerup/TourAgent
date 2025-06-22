# api/services/llm_service.py

import uuid
from typing import List, Dict, Any
from .llm_service_graph import app as graph_app, State as GraphState, RunnableConfig
from .llm_service_graph import START # 필요하다면

class BaseLLMService:  # LLM 서비스 인터페이스 정의
    """
    what: 다양한 LLM 구현체 교체를 위한 추상 클래스
    why: 구현 간 결합도를 낮추고 테스트 용이
    """
    def generate_session_metadata(self, first_message: str, **params) -> (str, str):  # 세션 메타데이터 생성 추상 메서드
        
        """
        what: 세션 메타데이터 생성 추상 메서드
        why: 서브클래스에서 구현해야 함
        """
        raise NotImplementedError  # 반드시 구현 필요
    
    def generate_bot_response(self, session_id: int, messages: List[Dict[str, Any]], **params) -> str:  # 봇 응답 생성 추상 메서드
        """8
        what: 봇 응답 생성 추상 메서드
        why: 서브클래스에서 구현해야 함
        """
        raise NotImplementedError  # 반드시 구현 필요

class DummyLLMService(BaseLLMService):
    """
    LangGraph 기반 LLM 서비스 구현체
    """
    def __init__(self):
        # graph_app는 compile된 StateGraph 인스턴스
        self.app = graph_app

    def generate_session_metadata(self, first_message: str, **params) -> (str, str):
        # 임시 thread_id 생성 (혹은 세션 ID를 사용할 수도 있음)
        thread_id = f"meta-{uuid.uuid4()}"
        # 초기 상태 지정
        init_state = GraphState(
            question=first_message,
            query="",
            answer="",
            messages=[],
            relevance="",
        )
        # RunnableConfig 설정
        config = RunnableConfig(configurable={"thread_id": thread_id})
        # START 노드부터 실행
        final = self.app.get_state(config, state=init_state).values
        meta = final.get("metadata", {})
        return meta.get("title", ""), meta.get("info", "")

    def generate_bot_response(self, session_id: int, messages: List[Dict[str, Any]], **params) -> str:
        # 재실행할 때는 같은 thread_id를 사용해 이전 상태를 복원하도록
        thread_id = str(session_id)
        # 이전 메시지가 graph에 체크포인트로 남아있다면 state 복원이 가능
        init_state = GraphState(
            question="",
            query="",
            answer="",
            messages=[m["content"] for m in messages],
            relevance="",
        )
        config = RunnableConfig(configurable={"thread_id": thread_id})
        final = self.app.get_state(config, state=init_state).values
        # 그래프의 bot_responses에 마지막 응답이 쌓여있다면 꺼내오기
        bot_responses = final.get("bot_responses", [])
        return bot_responses[-1] if bot_responses else ""

# class DummyLLMService(BaseLLMService):  # Dummy LLM 서비스 구현체
#     """
#     what: BaseLLMService를 상속한 더미 서비스
#     why: 실제 LLM 호출 전 스텁으로 사용
#     """
#     def __init__(self):  # 더미 서비스 초기화 메서드
#         """
#         what: 초기화
#         why: 추가 설정 필요 없으므로 pass 처리
#         """
#         pass

#     def generate_session_metadata(self, first_message, **params):  # 세션 제목 및 설명 더미 생성
#         """
#         what: 세션 제목 및 설명을 더미 생성하여 반환
#         why: 테스트용 메타데이터 생성
#         """
#         dummy_title = f"세션 더미: {first_message[:10]}..."  # 제목 생성
#         dummy_info = "이것은 더미 세션 설명입니다."  # 설명 생성
#         return dummy_title, dummy_info  # 반환

#     def generate_bot_response(self, session_id, messages, **params):  # 봇 응답 더미 생성
#         """
#         what: 봇 응답을 더미로 생성하여 반환
#         why: 테스트용 응답 생성
#         """
#         return "이것은 더미 봇 응답입니다."  # 고정 응답 반환