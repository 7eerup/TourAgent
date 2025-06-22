from rest_framework import serializers
from .models import Feedback
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

from django.contrib.auth.hashers import check_password       # 비밀번호 해시 비교 함수

class LoginSerializer(serializers.Serializer):
    # 클라이언트가 보낼 필드를 정의
    email = serializers.EmailField()                           # 이메일 형식 검증
    password = serializers.CharField(write_only=True)          # 비밀번호는 쓰기 전용

    def validate(self, attrs):
        # 1) 입력된 이메일/비밀번호 가져오기
        email = attrs.get('email')                             # 입력값 중 email
        password = attrs.get('password')                       # 입력값 중 password

        # 2) DB에서 해당 이메일의 User 조회 시도
        try:
            user = User.objects.get(email=email)               # email 기준으로 한 건 조회
        except User.DoesNotExist:
            # 존재하지 않으면 인증 실패
            raise serializers.ValidationError('이메일 또는 비밀번호 오류')

        # 3) 비밀번호 검증
        if not user.check_password(password):                  # 해시된 비밀번호 비교
            raise serializers.ValidationError('이메일 또는 비밀번호 오류')

        # 4) 검증 통과 시 validated_data에 user 객체 저장
        attrs['user'] = user
        return attrs                                           # 다음 단계에서 .validated_data 사용 가능


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model  = User
        fields = ('email', 'username', 'password', 'phone_number')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # → 추가 클레임
        token['username'] = user.username
        return token



    def validate(self, attrs):
        # 로그인 검증 로직을 수행하는 부모 validate 호출 (이때 토큰 발급됨)
        data = super().validate(attrs)
        # 응답 데이터(payload)에 추가 정보 삽입
        data['username'] = self.user.username                # 사용자 이름 추가
        data['id']       = self.user.id                      # 사용자 고유 ID 추가
        return data                                          # 확장된 응답 데이터 반환


#===========이하 채팅을 위한 직렬화기==================
from .models import ChatMessage, ChatSession                # what: ChatMessage 모델 임포트 why: 직렬화 대상 지정

class ChatSessionSerializer(serializers.ModelSerializer):
    # 모델의 id 필드를 API엔 'chat_session_id'로 노출, 읽기 전용
    chat_session_id = serializers.IntegerField(
        source='id', read_only=True
    )
    # 세션 소유자 User의 id를 'user_id'로 노출, 읽기 전용
    user_id = serializers.IntegerField(
        source='user.id', read_only=True
    )
    # 모델의 title 필드를 그대로 노출
    title = serializers.CharField()
    # 모델의 info 필드를 노출, 빈 문자열과 null 허용
    info = serializers.CharField(
        allow_blank=True, allow_null=True
    )
    # 모델의 parameters(JSONField) 필드를 그대로 노출
    parameters = serializers.JSONField()
    # 생성 시각(created_at)을 읽기 전용으로 노출
    created_at = serializers.DateTimeField(
        read_only=True
    )
    # 수정 시각(updated_at)을 읽기 전용으로 노출
    updated_at = serializers.DateTimeField(
        read_only=True
    )

    class Meta:
        model = ChatSession                             # 어떤 모델을 직렬화할지 지정
        fields = [                                      # API에 노출할 필드 목록
            'chat_session_id',
            'user_id',
            'title',
            'info',
            'parameters',
            'created_at',
            'updated_at',
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    # 모델의 id 필드를 'chat_message_id'로 노출, 읽기 전용
    chat_message_id   = serializers.IntegerField(
        source='id', read_only=True
    )
    # 모델의 order 필드를 'chat_order_number'로 노출
    chat_order_number = serializers.IntegerField(
        source='order'
    )
    # 모델의 sender 필드를 'chat_sender'로 노출
    chat_sender       = serializers.CharField(
        source='sender'
    )
    # 모델의 content 필드를 'message'로 노출
    message           = serializers.CharField(
        source='content'
    )
    # 모델의 created_at을 'message_time'으로 노출, 읽기 전용
    message_time      = serializers.DateTimeField(
        source='created_at', read_only=True
    )
    # 모델의 FK chatsession.id를 'chat_session_id'로 노출, 읽기 전용
    chat_session_id   = serializers.IntegerField(
        source='chatsession.id', read_only=True
    )

    class Meta:
        model = ChatMessage                             # 어떤 모델을 직렬화할지 지정
        fields = [                                      # API에 노출할 필드 목록
            'chat_message_id',
            'chat_order_number',
            'chat_sender',
            'message',
            'message_time',
            'chat_session_id',
        ]
        read_only_fields = [                            # 읽기 전용 필드 지정
            'chat_message_id',
            'message_time',
            'chat_session_id',
        ]

from .models import (                                                     # 사용할 모델들 한 번에 임포트
    ChatComponent,
    ChatInteraction,
    ChatSessionSummary,
    MessageEmbedding,
)

class ChatComponentSerializer(serializers.ModelSerializer):                # ChatComponent 모델용 Serializer 정의
    class Meta:                                                          # 내부 설정 모음
        model = ChatComponent                                            # 어떤 모델을 직렬화할지 지정
        fields = [                                                       # API에 노출할 필드 목록
            'id',                                                        # 컴포넌트 고유 ID
            'message',                                                   # 연관된 ChatMessage FK
            'component_type',                                            # 컴포넌트 종류 식별자
            'payload',                                                   # 렌더링에 필요한 JSON 데이터
            'order',                                                     # 컴포넌트 순서
        ]
        read_only_fields = [                                             # 클라이언트가 수정할 수 없는 필드
            'id',                                                        # PK 자동 생성
        ]

class ChatInteractionSerializer(serializers.ModelSerializer):             # ChatInteraction 모델용 Serializer 정의
    class Meta:
        model = ChatInteraction                                           # 어떤 모델을 직렬화할지 지정
        fields = [                                                       # 노출할 필드 목록
            'id',                                                        # 로그 고유 ID
            'message',                                                   # 연관된 ChatMessage 1:1 FK
            'llm_request',                                               # 호출에 사용된 페이로드
            'llm_response',                                              # LLM 응답 원본 페이로드
            'created_at',                                                # 로그 생성 시각
        ]
        read_only_fields = [                                             # 읽기 전용 필드 지정
            'id',                                                        # PK 자동 생성
            'created_at',                                                # 자동 기록 타임스탬프
        ]

class ChatSessionSummarySerializer(serializers.ModelSerializer):         # ChatSessionSummary 모델용 Serializer 정의
    class Meta:
        model = ChatSessionSummary                                        # 어떤 모델을 직렬화할지 지정
        fields = [                                                       # 노출할 필드 목록
            'id',                                                        # 요약 고유 ID
            'session',                                                   # 연관된 ChatSession 1:1 FK
            'summary_text',                                              # 자동 생성된 요약 문자열
            'updated_at',                                                # 요약 갱신 시각
        ]
        read_only_fields = [                                             # 읽기 전용 필드 지정
            'id',                                                        # PK 자동 생성
            'updated_at',                                                # 자동 기록 타임스탬프
        ]

class MessageEmbeddingSerializer(serializers.ModelSerializer):             # MessageEmbedding 모델용 Serializer 정의
    class Meta:
        model = MessageEmbedding                                          # 어떤 모델을 직렬화할지 지정
        fields = [                                                       # 노출할 필드 목록
            'id',                                                        # 임베딩 고유 ID
            'message',                                                   # 연관된 ChatMessage 1:1 FK
            'vector',                                                    # JSON 형태 임베딩 벡터
            'created_at',                                                # 임베딩 생성 시각
        ]
        read_only_fields = [                                             # 읽기 전용 필드 지정
            'id',                                                        # PK 자동 생성
            'created_at',                                                # 자동 기록 타임스탬프
        ]
        
        
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Feedback
        fields = ['is_liked']