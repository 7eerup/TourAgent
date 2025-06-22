# api/tests.py

from rest_framework.test import APITestCase                   # what: DRF 테스트 클래스 임포트 why: API 테스트 편의 제공
from django.urls import reverse                               # what: reverse 임포트 why: URL 동적 생성
from .models import ChatSession, ChatMessage                  # what: 모델 임포트 why: 테스트 데이터 생성

class ChatMessageAPITest(APITestCase):                        # what: APITestCase 서브클래스 정의 why: API 테스트 환경 구성
    def setUp(self):                                          # what: 테스트 초기화 메서드 why: 공통 테스트 데이터 준비
        self.session = ChatSession.objects.create(            # what: 테스트용 세션 생성 why: 메시지 저장소 역할
            chat_session_title='테스트 세션'                  
        )
        self.url = reverse(                                   # what: 메시지 목록 URL 생성 why: 하드코딩 방지
            'chat-session-messages', 
            kwargs={'session_pk': self.session.pk}
        )

    def test_create_and_list(self):                           # what: 생성·조회 흐름 검증 테스트 why: API 기능 확인
        payload = {                                          # what: 요청 페이로드 정의 why: POST 데이터 준비
            'chat_order_number': 1,
            'chat_sender': 'user',
            'message': '안녕하세요',
            'message_type': 'text',
        }
        create_resp = self.client.post(self.url, payload)    # what: POST 요청 실행 why: 메시지 생성
        self.assertEqual(create_resp.status_code, 201)       # what: 응답 코드 검증 why: 생성 성공 여부 확인

        list_resp = self.client.get(self.url)                # what: GET 요청 실행 why: 목록 조회
        self.assertEqual(list_resp.status_code, 200)         # what: 응답 코드 검증 why: 조회 성공 여부 확인
        self.assertEqual(len(list_resp.data), 1)             # what: 반환 데이터 개수 확인 why: 메시지 1건 존재 확인
