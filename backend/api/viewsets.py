# api/viewsets.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins            # what: ViewSet·Mixin 임포트 why: CRUD 재사용성 확보
from .models import ChatMessage                        # what: ChatMessage 모델 임포트 why: 데이터 저장·조회
from .serializers import ChatMessageSerializer         # what: Serializer 임포트 why: JSON 변환 일관성 유지
from .services.llm_service import BaseLLMService, DummyLLMService  # what: LLM 서비스 인터페이스 및 구현 임포트 why: 의존성 분리

class ChatMessageViewSet(
    mixins.CreateModelMixin,  # Enable POST create
    mixins.ListModelMixin,    # Enable GET list
    
    viewsets.GenericViewSet   # Core ViewSet class
):
    serializer_class = ChatMessageSerializer  # Serializer for input/output

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inject LLM service dependency
        self.llm_service = DummyLLMService()

    def get_queryset(self):
        user_pk    = self.kwargs['user_pk']
        session_pk = self.kwargs['session_pk']
        return ChatMessage.objects.filter(
            chatsession__user_id=user_pk,
            chatsession_id=session_pk
        ).order_by('order')

    def perform_create(self, serializer):
        # Save new user message with FK to parent session
        instance = serializer.save(chatsession_id=self.kwargs['session_pk'])
        if instance.sender == 'user':
            # Generate assistant reply only for user messages
            reply_text = self.llm_service.generate_response(instance)
            # Save assistant message in same session
            ChatMessage.objects.create(
                chatsession_id=instance.chatsession_id,
                order=instance.order + 1,
                sender='assistant',
                content=reply_text
            )

from rest_framework import permissions                       # DRF ViewSet 및 권한 관리 임포트
from .models import ChatSession                                       # ChatSession 모델 임포트: 쿼리 및 생성용
from .serializers import ChatSessionSerializer                        # ChatSessionSerializer 임포트: 변환 로직

class ChatSessionViewSet(viewsets.ModelViewSet):                      # ModelViewSet 상속: CRUD 기능 일괄 제공
    queryset = ChatSession.objects.all()                              # 기본 쿼리셋: 전체 세션(필터링은 get_queryset에서)
    serializer_class = ChatSessionSerializer                          # 직렬화기 연결
    # permission_classes = [permissions.IsAuthenticated]                # 로그인한 사용자만 접근 허용

    def get_queryset(self):                                           # 쿼리셋 커스터마이징
        user_pk = self.kwargs['user_pk']
        # user__pk 대신 user_id=user_pk 도 가능
        return ChatSession.objects.filter(user_id=user_pk).order_by('-created_at')

    def perform_create(self, serializer):                             # 데이터 저장 직전 추가 처리
        # 세션 생성 시 user 필드를 현재 로그인 사용자로 지정
        serializer.save(user=self.request.user)

from .models import (                                                    # 사용할 모델들 한 번에 임포트
    ChatComponent,
    ChatInteraction,
    ChatSessionSummary,
    MessageEmbedding,
)
from .serializers import (                                               # 방금 만든 직렬화기들 임포트
    ChatComponentSerializer,
    ChatInteractionSerializer,
    ChatSessionSummarySerializer,
    MessageEmbeddingSerializer,
)

class ChatComponentViewSet(viewsets.ModelViewSet):                       # ChatComponent CRUD 전용 ViewSet
    serializer_class = ChatComponentSerializer

    def get_queryset(self):
        user_pk    = self.kwargs['user_pk']
        session_pk = self.kwargs['session_pk']
        message_pk = self.kwargs['message_pk']
        return ChatComponent.objects.filter(
            chatmessage__chatsession__user_id=user_pk,
            chatmessage__chatsession_id=session_pk,
            chatmessage_id=message_pk
        )
    def perform_create(self, serializer):
        # FK 연결
        message = get_object_or_404(
            ChatMessage,
            id=self.kwargs['message_pk'],
            chatsession__user_id=self.kwargs['user_pk'],
            chatsession_id=self.kwargs['session_pk']
        )
        serializer.save(chatmessage=message)

class ChatInteractionViewSet(viewsets.ModelViewSet):                     # ChatInteraction CRUD 전용 ViewSet
    serializer_class = ChatInteractionSerializer

    def get_queryset(self):
        user_pk    = self.kwargs['user_pk']
        session_pk = self.kwargs['session_pk']
        message_pk = self.kwargs['message_pk']
        return ChatInteraction.objects.filter(
            chatmessage__chatsession__user_id=user_pk,
            chatmessage__chatsession_id=session_pk,
            chatmessage_id=message_pk
        )

    def perform_create(self, serializer):
        message = get_object_or_404(
            ChatMessage,
            id=self.kwargs['message_pk'],
            chatsession__user_id=self.kwargs['user_pk'],
            chatsession_id=self.kwargs['session_pk']
        )
        serializer.save(chatmessage=message)

class ChatSessionSummaryViewSet(viewsets.ModelViewSet):                  # ChatSessionSummary CRUD 전용 ViewSet
    serializer_class = ChatSessionSummarySerializer

    def get_queryset(self):
        user_pk    = self.kwargs['user_pk']
        session_pk = self.kwargs['session_pk']
        return ChatSessionSummary.objects.filter(
            chatsession__user_id=user_pk,
            chatsession_id=session_pk
        )

    def perform_create(self, serializer):
        session = get_object_or_404(
            ChatSession,
            id=self.kwargs['session_pk'],
            user_id=self.kwargs['user_pk']
        )
        serializer.save(chatsession=session)

class MessageEmbeddingViewSet(viewsets.ModelViewSet):                    # MessageEmbedding CRUD 전용 ViewSet
    serializer_class = MessageEmbeddingSerializer

    def get_queryset(self):
        user_pk    = self.kwargs['user_pk']
        session_pk = self.kwargs['session_pk']
        message_pk = self.kwargs['message_pk']
        return MessageEmbedding.objects.filter(
            chatmessage__chatsession__user_id=user_pk,
            chatmessage__chatsession_id=session_pk,
            chatmessage_id=message_pk
        )

    def perform_create(self, serializer):
        message = get_object_or_404(
            ChatMessage,
            id=self.kwargs['message_pk'],
            chatsession__user_id=self.kwargs['user_pk'],
            chatsession_id=self.kwargs['session_pk']
        )
        serializer.save(chatmessage=message)