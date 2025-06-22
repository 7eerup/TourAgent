# api/services/llm_service.py
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
os.environ["GOOGLE_API_KEY"] = os.getenv("KNY_GOOGLE_API_KEY")
# GOOGLE_API_KEY = load_dotenv(find_dotenv())

import re
def _clean_markdown_json(content: str) -> str:
    """
    ```json
    { … }
    ```
    같은 fenced code block 을 벗겨내고 순수 JSON 문자열만 반환합니다.
    """
    # 1) ```json … ``` 블록 캡쳐
    fence_re = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
    m = fence_re.search(content)
    if m:
        return m.group(1)

    # 2) 혹시 ``` 없이 그냥 json만 돌려줬다면
    return content.strip()


class BaseLLMService:  # LLM 서비스 인터페이스 정의
    """
    what: 다양한 LLM 구현체 교체를 위한 추상 클래스
    why: 구현 간 결합도를 낮추고 테스트 용이
    """
    def generate_session_metadata(self, first_message, **params):  # 세션 메타데이터 생성 추상 메서드
        """
        what: 세션 메타데이터 생성 추상 메서드
        why: 서브클래스에서 구현해야 함
        """
        raise NotImplementedError  # 반드시 구현 필요

    def generate_bot_response(self, session_id, messages, **params):  # 봇 응답 생성 추상 메서드
        """
        what: 봇 응답 생성 추상 메서드
        why: 서브클래스에서 구현해야 함
        """
        raise NotImplementedError  # 반드시 구현 필요

class DummyLLMService(BaseLLMService):  # Dummy LLM 서비스 구현체
    """
    what: BaseLLMService를 상속한 더미 서비스
    why: 실제 LLM 호출 전 스텁으로 사용
    """
    def __init__(self):  # 더미 서비스 초기화 메서드
        """
        what: 초기화
        why: 추가 설정 필요 없으므로 pass 처리
        """
        pass

    def generate_session_metadata(self, first_message, **params):  # 세션 제목 및 설명 더미 생성
        """
        what: 세션 제목 및 설명을 더미 생성하여 반환
        why: 테스트용 메타데이터 생성
        """
        dummy_title = f"세션 더미: {first_message[:10]}..."  # 제목 생성
        dummy_info = "이것은 더미 세션 설명입니다."  # 설명 생성
        return dummy_title, dummy_info  # 반환

    def generate_bot_response(self, session_id, messages, **params):
        user_input = messages[-1]['content']
        # 모드 키워드 파악
        include_marker = '지도모드' in user_input
        include_text = '채팅모드' in user_input or '텍스트모드' in user_input
        include_form = '폼모드' in user_input

        deltas = []
        # marker 모드
        if include_marker:
            deltas.append({
                'type': 'map_marker',
                'payload': {'lat': 37.56, 'lng': 126.97, 'label': '서울'}
            })
        # text 모드
        if include_text:
            deltas.append({
                'type': 'text',
                'payload': {'content': '여기는 텍스트 응답입니다.\n'}
            })
        # form 모드
        if include_form:
            deltas.append({
                'type': 'form',
                'payload': {'fields': [
                    {'name': 'email', 'label': '이메일', 'type': 'email'},
                    {'name': 'name', 'label': '이름', 'type': 'text'}
                ]}
            })
        # 기본 모드(아무 모드도 없을 때)
        if not any([include_marker, include_text, include_form]):
            deltas.append({
                'type': 'text',
                'payload': {'content': '이것은 기본 응답입니다.\n'}
            })
        # 끝 델타
        deltas.append({'type': 'end', 'payload': {}})
        return deltas

import json
from typing import Any, Dict, List, Tuple

from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI

class ss_LLMService(BaseLLMService):
    """
    LLM 호출을 추상화한 서비스 클래스
    generate_session_metadata: 세션 제목과 초기 사용자 메시지(info) 생성
    generate_bot_response: 봇 응답 델타 생성
    """
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash-preview-05-20",
        temperature: float = 0.5,
        max_retries: int = 2,
    ) -> None:
        """
        Initializes LLMService with the specified model and parameters.

        Args:
            model_name: Identifier for Google Gemini model.
            temperature: Sampling temperature for generation.
            max_retries: Number of attempts to parse JSON.
        """
        self.model_name = model_name
        self.max_retries = max_retries
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=max_retries,
        )
        self._build_prompt_template()

    def _build_prompt_template(self) -> None:
        """
        Constructs the few-shot prompt template for session metadata generation.
        """
        # 시스템 역할 프롬프트 생성: 모델 역할과 출력 형식 지정
        system_text = (
            "You are a travel session creator assistant.\n"
            "답변 생성은 한국어로 합니다.\n"
            "Given session parameters, output only a JSON object with 'title' and 'info'.\n"
            "Combine the district, schedule, and theme when generating the title, summarizing the theme as a keyword\n"
            "In the info field, insert '\\n\\n' after each sentence for readability.\n"
            "Always use a casual tone instead of a formal one. Stick to informal language without exception.\n"
            "Do not use the word \"현지\". Refrain from using phrases or tones typically associated with international travel. Instead, generate it in a style that people on short domestic trips would use."
        )  # system_text 변수에 시스템 메시지 작성
        system_template = PromptTemplate(
            template=system_text,
            input_variables=[],
        )  # PromptTemplate 객체로 변환
        self.system_prompt = SystemMessagePromptTemplate(
            prompt=system_template
        )  # SystemMessagePromptTemplate 감싸기

        # 첫 번째 예시 파라미터: 서울 강남구 맛집 여행
        self.example_params = json.dumps(
            {
                "city": "서울",
                "district": "강남구",
                "theme": "맛집 여행",
                "startDate": "2025-07-10",
                "endDate": "2025-07-15",
                "companions": "친구, 가족",
                "groupSize": 4,
                "mealSchedule": ["아침", "저녁"],
            },
            ensure_ascii=False,
        )  # JSON 문자열로 인코딩된 예시 파라미터
        self.example_output = json.dumps(
            {
                "title": "강남구 5박6일 맛집 기행",
                "info": (
                    # 예시 출력 정보
                    '우리 가족 3~4명이 7월 10일부터 15일까지 서울 강남구에서 ‘맛집 여행’ 테마로 여행할 계획이야.\n\n'
                    '아침과 저녁은 숙소에서 해결하고, 점심은 맛집에서 즐길 예정이야.\n\n'
                    '강남구의 대표 맛집과 추천 코스 일정을 제안해줘.'
                ),
            },
            ensure_ascii=False,
        )  # JSON 문자열로 인코딩된 예시 출력
        example_template = PromptTemplate(
            template=(
                "Example parameters:\n{example_params}\n"
                "Example JSON output:\n{example_output}\n"
            ),
            input_variables=["example_params", "example_output"],
        )  # 예시용 HumanMessage Prompt 생성
        self.example_user = HumanMessagePromptTemplate(
            prompt=example_template
        )  # HumanMessagePromptTemplate 포장
        self.example_ai = AIMessagePromptTemplate(
            prompt=PromptTemplate(
                template="{example_output}",
                input_variables=["example_output"],
            )
        )  # AIMessagePromptTemplate 포장

        # 두 번째 예시 파라미터: 부산 해운대구 해변 산책 여행
        self.example_params_2 = json.dumps(
            {
                "city": "부산",
                "district": "해운대구",
                "theme": "해변 산책",
                "startDate": "2025-08-01",
                "endDate": "2025-08-03",
                "companions": "커플",
                "groupSize": 2,
                "mealSchedule": ["아침", "점심", "저녁"],
            },
            ensure_ascii=False,
        )  # 두 번째 예시 파라미터 JSON
        self.example_output_2 = json.dumps(
            {
                "title": "해운대구 2박3일 해변 산책 여행",
                "info": (
                    "우리 커플은 8월 1일부터 3일까지 부산 해운대구에서 '해변 산책' 테마로 여행할 거야.\n\n"
                    "아침, 점심, 저녁 모두 제대로 즐기면서 바닷가 산책과 함께 현지 맛집도 경험해보자.\n\n"
                    "해운대구의 인기 맛집과 추천 산책 코스를 제안해줘."
                )
            },
            ensure_ascii=False,
        )  # 두 번째 예시 출력 JSON
        example_template_2 = PromptTemplate(
            template=(
                "Example parameters:\n{example_params_2}\n"
                "Example JSON output:\n{example_output_2}\n"
            ),
            input_variables=["example_params_2", "example_output_2"],
        )  # 두 번째 예시용 PromptTemplate
        self.example_user_2 = HumanMessagePromptTemplate(
            prompt=example_template_2
        )  # 두 번째 예시 HumanMessagePromptTemplate
        self.example_ai_2 = AIMessagePromptTemplate(
            prompt=PromptTemplate(
                template="{example_output_2}",
                input_variables=["example_output_2"],
            )
        )  # 두 번째 예시 AIMessagePromptTemplate

        # 실제 사용자 입력을 위한 프롬프트
        real_template = PromptTemplate(
            template=(
                "Actual parameters:\n{params}\n"
                "JSON output:\n"
            ),
            input_variables=["params"],
        )  # 사용자 입력 파라미터 템플릿
        self.real_user = HumanMessagePromptTemplate(
            prompt=real_template
        )  # 실제 사용자 프롬프트 포장

        # 메시지 시퀀스를 시스템, 예시1, 예시1 출력, 예시2, 예시2 출력, 실제 사용자 순으로 결합
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                self.system_prompt,
                self.example_user,
                self.example_ai,
                self.example_user_2,
                self.example_ai_2,
                self.real_user,
            ]
        )  # 최종 ChatPromptTemplate 생성


    def generate_session_metadata(
        self, session_parameters: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Generates a session title and info string based on session parameters.

        Args:
            session_parameters: Dictionary of user-supplied session parameters.

        Returns:
            A tuple of (title, info) extracted from the LLM's JSON output.

        Raises:
            ValueError: If LLM fails to return parseable JSON after retries.
        """
        params_json = json.dumps(session_parameters, ensure_ascii=False)
        messages = self.prompt_template.format_prompt(
            example_params=self.example_params,
            example_output=self.example_output,
            example_params_2=self.example_params_2,
            example_output_2=self.example_output_2,
            params=params_json,
        ).to_messages()
        print(">> prompt messages repr:", repr(messages))
        print(">> prompt messages types:", [type(m) for m in messages])

        for idx, m in enumerate(messages):
            print(f">> idx={idx}, element repr={repr(m)}")

        for attempt in range(self.max_retries):
            # result = self.llm(messages)
            result = self.llm.invoke(messages)   # deprecated 경고 해결 위해 __call__ 대신 invoke 사용
            print("LLM raw content:", repr(result.content))
            # 1) 마크다운 fence 제거
            clean_content = _clean_markdown_json(result.content)
            try:
                parsed = json.loads(clean_content)
                return parsed.get("title", ""), parsed.get("info", "")
            except json.JSONDecodeError:
                if attempt == self.max_retries - 1:
                    raise ValueError("Failed to parse JSON from LLM response")

    def generate_bot_response(
        self,
        session_id: int,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Creates a list of response deltas for the assistant's reply.

        Args:
            session_id: Identifier for the chat session.
            messages: List of previous messages (dicts with 'sender' and 'content').

        Returns:
            A list of delta dictionaries, each with 'type' and 'payload'.
        """
        deltas: List[Dict[str, Any]] = []
        combined_text = "".join(msg["content"] for msg in messages)
        deltas.append({
            "type": "text",
            "payload": {"content": f"Echo: {combined_text}"},
        })
        return deltas

    # def generate_bot_response(self, session_id, messages, **params):
    #     """
    #     기존 메시지 이력과 파라미터를 받아 봇 응답 델타 리스트 반환
    #     (실제로 델타 스트림을 처리하는 부분은 구현 필요)
    #     """
    #     # 간단 예시: 클라이언트로부터 받은 message를 그대로 echo
    #     # 실제로는 self.llm.stream(...) 등을 사용해 델타 스트림 처리
    #     deltas = []
    #     # 요청 메시지 합치기
    #     combined = "".join(msg['content'] for msg in messages)
    #     # 예시 텍스트 델타 생성
    #     deltas.append({
    #         'type': 'text',
    #         'payload': {'content': f"Echo: {combined}"}
    #     })
    #     return deltas
