from django.db import transaction                               # DB 트랜잭션 관리용

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError


class TokenVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token') or request.COOKIES.get("access_token")

        if not token:
            return Response({"detail": "Token is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            AccessToken(token)  # 검증 시도
            return Response({"detail": "Token is valid."}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class    = RegisterSerializer
    permission_classes  = (permissions.AllowAny,)

    def perform_create(self, serializer):
        # 단일 서버 환경에서는 REMOTE_ADDR만 사용
        client_ip = self.request.META.get('REMOTE_ADDR')
        serializer.save(joined_ip=client_ip)


class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer      # JWT 토큰 시리얼라이저 사용
    permission_classes = (permissions.AllowAny,)            # 로그인은 누구나 요청 가능

# '''
# class LogoutAPIView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         refresh_token = request.data.get("refresh")
#         if not refresh_token:
#             return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             token = RefreshToken(refresh_token)
#             token.blacklist()  # 블랙리스트에 등록
#             return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
#         except TokenError:
#             return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
# '''


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.COOKIES.get("refresh_token")
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            pass  # 이미 만료 or 블랙리스트

        res = Response({"detail": "logout"}, status=205)
        res.delete_cookie("refresh_token")
        res.delete_cookie("access_token")
        return res

class CookieLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer  # 이미 만든 것 재사용

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # access/refresh in body
        data = response.data
        refresh = data.pop("refresh")          # 쿠키로 이동
        access  = data.pop("access")           # 그대로 body 또는 헤더

        # HttpOnly 쿠키 설정 (7일)
        response.set_cookie(
            "refresh_token",
            refresh,
            httponly=True,
            secure=True,          # HTTPS 권장
            samesite="Lax",
            max_age=60*60*24*7,
        )
        # 선택: access 도 쿠키로
        response.set_cookie(
            "access_token",
            access,
            httponly=False,       # JS 읽어서 Authorization 헤더에 실어도 OK
            secure=True,
            samesite="Lax",
            max_age=60*15,
        )
        return response

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

class CookieRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        request.data["refresh"] = request.COOKIES.get("refresh_token")
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            new_access = response.data.pop("access")
            # 새 access 쿠키 덮어쓰기
            response.set_cookie(
                "access_token",
                new_access,
                httponly=False,
                secure=True,
                samesite="Lax",
                max_age=60*15,
            )
        return response


#===채팅 테이블 관련 기본 CRUD는 뷰셋에 있고, 여기에는 커스텀 API 구현이 여기에 들어갑니다===
from .models import ChatSession, ChatMessage                              # 사용하는 모델 임포트
from .serializers import ChatSessionSerializer, ChatMessageSerializer     # 직렬화기 임포트
from .services.llm_service import DummyLLMService          # 더미 LLM 서비스 구현체 import
from django.views.decorators.csrf import csrf_exempt  # CSRF 예외 처리

class ChatSessionStartAPIView(APIView):
    """
    POST /api/v1/chat-sessions/start/
    시작된 채팅 세션과 첫 메시지를 생성하는 API
    """
    permission_classes = [permissions.IsAuthenticated]  # 인증된 요청만 허용

    def post(self, request):
        # Extract session parameters and initial user message
        params = request.data.get('session_parameters', {})
        user_msg = request.data.get('message')
        user = request.user

        # Initialize LLM service and generate session metadata (title, info)
        llm_service = DummyLLMService()
        title, info = llm_service.generate_session_metadata(
            first_message=user_msg,
            **params
        )

        # Save session and first user message atomically
        with transaction.atomic():
            session = ChatSession.objects.create(
                user=user,            # 참조된 유저 객체
                title=title,          # LLM이 생성한 세션 제목
                info=info,            # LLM이 생성한 세션 설명
                parameters=params     # 세션 옵션 저장
            )
            user_message = ChatMessage.objects.create(
                chatsession=session,  # FK 필드명으로 updated model 사용
                order=0,              # 첫 메시지이므로 순서 0
                sender='user',        # 'user' 역할 지정
                content=user_msg      # 사용자가 보낸 메시지 내용
            )

        # Generate bot response using LLM service
        bot_content = llm_service.generate_bot_response(
            session_id=session.id,              # 세션 고유 ID
            messages=[{'sender':'user','content':user_msg}],
            **params
        )

        # Save bot message atomically
        with transaction.atomic():
            bot_message = ChatMessage.objects.create(
                chatsession=session,               # 같은 세션 참조
                order=user_message.order + 1,      # 다음 순서
                sender='assistant',                # 'assistant' 역할 지정
                content=bot_content                # LLM 응답 내용 저장
            )

        # Serialize and return created session and messages
        session_data = ChatSessionSerializer(session).data
        messages_data = [
            ChatMessageSerializer(user_message).data,
            ChatMessageSerializer(bot_message).data,
        ]
        return Response(
            {'session': session_data, 'messages': messages_data},
            status=status.HTTP_201_CREATED
        )

class ChatSessionMessageAPIView(APIView):
    """
    POST /api/v1/chat-sessions/{session_id}/messages/
    기존 채팅 세션에 새 메시지 추가 후 봇 응답 생성하는 API
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        # Load existing session by PK
        session = ChatSession.objects.get(id=session_id)

        # Save user message
        user_msg = request.data.get('message')
        user_message = ChatMessage.objects.create(
            chatsession=session,      # FK field 업데이트
            order=session.messages.count(),  # 현재 메시지 수 기반 순서
            sender='user',                   # 'user' 역할 지정
            content=user_msg                 # 메시지 본문 저장
        )

        # Generate bot response
        llm_service = DummyLLMService()
        bot_content = llm_service.generate_bot_response(
            session_id=session.id,
            messages=[{'sender':'user','content':user_msg}],
            **session.parameters             # 세션 옵션 재사용
        )

        # Save bot message
        bot_message = ChatMessage.objects.create(
            chatsession=session,
            order=user_message.order + 1,    # 다음 순서
            sender='assistant',              # 'assistant' 역할 지정
            content=bot_content              # LLM 응답 저장
        )

        # Serialize and respond
        messages_data = [
            ChatMessageSerializer(user_message).data,
            ChatMessageSerializer(bot_message).data,
        ]
        return Response({'messages': messages_data}, status=status.HTTP_200_OK)