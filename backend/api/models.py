# Django의 ORM 기능을 사용하기 위해 models 모듈을 import
from django.db import models                       # Django ORM 기본 임포트
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth import get_user_model  # What: 프로젝트 설정의 User 모델을 참조하기 위해 임포트
from django.db.models import JSONField                        # Django 3.1+ 내장 JSONField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)          #  해시 저장
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email        = models.EmailField(unique=True)
    username     = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    joined_at    = models.DateTimeField(auto_now_add=True)
    joined_ip    = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email

# What: 현재 프로젝트에 지정된 User 모델을 가져옴
# Why: AbstractBaseUser 등 커스텀 모델이든 일관된 참조를 위해 사용
User = get_user_model()



class ChatSession(models.Model):
    # PK: Django 기본 id 사용 → 별도 선언 불필요
    user        = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    title       = models.CharField(max_length=200)
    info        = models.TextField(null=True, blank=True)
    parameters  = models.JSONField(default=dict, blank=True)  # JSONField 이름 단축
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.id} – {self.title}"

class Feedback(models.Model):
    """사용자 피드백(좋아요/싫어요) 저장"""
    session   = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name='feedbacks'
    )
    is_liked  = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['session', 'is_liked'])]

class ChatMessage(models.Model):
    # PK: Django 기본 id
    chatsession     = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    order       = models.PositiveIntegerField(default=0)
    sender      = models.CharField(
        max_length=20,
        choices=[('user','user'),('assistant','assistant')],
        default='user'
    )
    content     = models.TextField(blank=True)                  # text → content로 명칭 통일
    metadata    = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)       # timestamp → created_at으로 통일

    class Meta:
        ordering = ['order']  # 기본 정렬 옵션

class ChatComponent(models.Model):
    chatmessage     = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='components'
    )
    component_type = models.CharField(max_length=50)
    payload     = models.JSONField(default=dict)
    order       = models.PositiveIntegerField(default=0)

class ChatInteraction(models.Model):
    chatmessage     = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='interaction'
    )
    request     = models.JSONField()  # llm_request → request
    response    = models.JSONField()  # llm_response → response
    created_at  = models.DateTimeField(auto_now_add=True)

class ChatSessionSummary(models.Model):
    chatsession     = models.OneToOneField(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='summary'
    )
    summary     = models.TextField()  # summary_text → summary
    updated_at  = models.DateTimeField(auto_now=True)

class MessageEmbedding(models.Model):
    chatmessage     = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='embedding'
    )
    vector      = models.JSONField()  # 이름 간결화
    created_at  = models.DateTimeField(auto_now_add=True)


'''======채팅의 고도화를 분리하기위한 DB 재구성======
class ChatSession(models.Model):  # What: 대화 세션(챗방) 단위 데이터 모델
    # Why: 사용자가 여러 개의 채팅 세션을 생성·관리할 수 있도록 분리
    chat_session_id     = models.AutoField(
        primary_key=True  # What: 세션 고유 ID, MariaDB INT AutoIncrement
        # Why: 기본키로 지정하여 자동 증가 사용
    )
    user                = models.ForeignKey(
        User,  # What: 세션 소유자 참조
        on_delete=models.CASCADE,  # What: 유저 삭제 시 세션도 함께 삭제
        related_name='chat_sessions'  # What: User 객체에서 세션 역참조
        # Why: 데이터 무결성 및 ORM 역참조 편의성 제공
    )
    title               = models.CharField(
        max_length=200,  # What: 세션 제목 저장
        verbose_name='Chat Session Title'  # What: Admin UI 필드명
        # Why: 저장 공간 최적화 및 관리 편의성 제공
    )
    info                = models.TextField(
        null=True,
        verbose_name="Chat Session Info"
    )
    session_parameters  = JSONField(
        default=dict,                                         
        blank=True,
        verbose_name="Session Parameters",
        help_text="장소, 일정, 인원, 컨셉 등 세션 공통 파라미터"
    )
    created_at          = models.DateTimeField(
        auto_now_add=True  # What: 세션 생성 시각 자동 기록
        # Why: 기록 보관 및 정렬 등에 사용
    )
    updated_at          = models.DateTimeField(
        auto_now=True  # What: 세션 수정 시각 자동 갱신
        # Why: 최신 상태 추적 및 변경 이력 관리
    )
class ChatMessage(models.Model):  # What: 개별 채팅 메시지 모델
    # Why: 사용자/어시스턴트 간 교환된 콘텐츠와 메타데이터 저장
    id = models.AutoField(
        primary_key=True  # What: 메시지 고유 ID, AutoIncrement
        # Why: 순차적 저장 및 기본키 역할
    )
    session = models.ForeignKey(
        ChatSession,  # What: 메시지가 속한 세션 참조
        on_delete=models.CASCADE,  # What: 세션 삭제 시 메시지 자동 삭제
        related_name='messages'  # What: ChatSession에서 메시지 역참조
        # Why: ORM 편의성 및 데이터 무결성 보장
    )
    order = models.PositiveIntegerField(
        default=0,  # What: 세션 내 메시지 순서
        verbose_name='Order in Session'  # What: Admin UI 필드명
        # Why: 메시지 렌더링 순서 제어
    )
    sender = models.CharField(
        max_length=20,                  # What: 발신 주체를 나타내는 문자열 길이
        choices=[                       # What: 허용 가능한 값의 목록
            ('user', 'user'),
            ('assistant', 'assistant'),
        ],
        default='user',                 # What: 신규 생성되는 모든 레코드는 기본값 'user' 사용
        null=False,                     # Why: 기존 데이터에 NULL 이 없어야 함을 보장
        blank=False,                    # Why: 폼 검증 시 반드시 값이 있어야 함
        verbose_name="Chat Sender",     # What: 관리자 화면 등에 표시될 필드 이름
        help_text="메시지 발신 주체. 'user' 또는 'assistant'",  # Why: 필드 목적 및 허용값 설명
    )
    text = models.TextField(
        blank=True,  # What: 메시지 텍스트
        verbose_name='Text Content'  # What: Admin UI 필드명
        # Why: UI 컴포넌트 전용 메시지 허용
    )
    metadata = models.JSONField(
        default=dict,  # What: 자유 구조 메타데이터 저장
        blank=True,  # What: 메타데이터 없는 메시지 허용
        verbose_name='Metadata'  # What: Admin UI 필드명
        # Why: 스타일, 버튼, 지도 정보 등 확장성 제공
    )
    timestamp = models.DateTimeField(
        auto_now_add=True  # What: 메시지 저장 시각 자동 기록
        # Why: 시간 순 정렬 및 이력 관리
    )
class ChatComponent(models.Model):  # What: 메시지 내 UI 컴포넌트 모델
    # Why: 지도, 달력, 버튼 등 복합 UI 액션을 메시지와 분리하여 저장
    id = models.AutoField(
        primary_key=True  # What: 컴포넌트 고유 ID
        # Why: AutoIncrement로 식별 및 기본키 역할
    )
    message = models.ForeignKey(
        ChatMessage,  # What: 소속 메시지 참조
        on_delete=models.CASCADE,  # What: 메시지 삭제 시 컴포넌트 삭제
        related_name='components'  # What: ChatMessage에서 컴포넌트 역참조
        # Why: ORM 편의성 및 데이터 무결성 제공
    )
    component_type = models.CharField(
        max_length=50,  # What: 컴포넌트 유형 식별자
        verbose_name='Component Type'  # What: Admin UI 필드명
        # Why: 다양한 UI 액션 식별 및 처리 로직 분기
    )
    payload = models.JSONField(
        default=dict,  # What: 컴포넌트 렌더링 데이터 저장
        verbose_name='Payload'  # What: Admin UI 필드명
        # Why: 위치 정보, 이미지 URL 등 다양한 데이터 수용
    )
    order = models.PositiveIntegerField(
        default=0,  # What: 메시지 내 컴포넌트 순서
        verbose_name='Order in Message'  # What: Admin UI 필드명
        # Why: 렌더링 순서 제어
    )
class ChatInteraction(models.Model):  # What: LLM 호출 로그 모델
    # Why: 디버깅 및 성능 분석을 위해 요청/응답 원본 보관
    id = models.AutoField(
        primary_key=True  # What: 로그 고유 ID
        # Why: AutoIncrement로 식별 및 기본키 역할
    )
    message = models.OneToOneField(
        ChatMessage,  # What: 대응되는 어시스턴트 메시지
        on_delete=models.CASCADE,  # What: 메시지 삭제 시 로그 삭제
        related_name='interaction'  # What: ChatMessage에서 로그 역참조
        # Why: 메시지-로그 1:1 매핑 보장
    )
    llm_request = models.JSONField(
        verbose_name='LLM Request Payload'  # What: 호출에 사용된 JSON 페이로드 저장
        # Why: 동일 조건 재현 및 디버깅용
    )
    llm_response = models.JSONField(
        verbose_name='LLM Response Payload'  # What: LLM 응답 원본 JSON 저장
        # Why: 결과 검증 및 분석을 위해 원본 유지
    )
    created_at = models.DateTimeField(
        auto_now_add=True  # What: 로그 생성 시각 자동 기록
        # Why: 이벤트 타임라인 분석에 사용
    )
class ChatSessionSummary(models.Model):  # What: 대화 세션 요약 모델
    # Why: 긴 대화를 간략히 보여주어 UX 및 RAG 컨텍스트 최적화
    id = models.AutoField(
        primary_key=True  # What: 요약 고유 ID
        # Why: AutoIncrement로 식별 및 기본키 역할
    )
    session = models.OneToOneField(
        ChatSession,  # What: 요약 대상 세션 참조
        on_delete=models.CASCADE,  # What: 세션 삭제 시 요약 삭제
        related_name='summary'  # What: ChatSession에서 요약 역참조
        # Why: 세션-요약 1:1 매핑 유지
    )
    summary_text = models.TextField(
        verbose_name='Summary Text'  # What: LLM 생성 세션 요약 저장
        # Why: 빠른 컨텍스트 이해 및 비용 절감
    )
    updated_at = models.DateTimeField(
        auto_now=True  # What: 요약 갱신 시각 자동 기록
        # Why: 최신 요약 유지
    )
class MessageEmbedding(models.Model):  # What: 메시지 임베딩 벡터 저장 모델
    # Why: RAG 검색을 위한 벡터 인덱싱 데이터 보관
    id = models.AutoField(
        primary_key=True  # What: 임베딩 고유 ID
        # Why: AutoIncrement로 식별 및 기본키 역할
    )
    message = models.OneToOneField(
        ChatMessage,  # What: 임베딩 대상 메시지 참조
        on_delete=models.CASCADE,  # What: 메시지 삭제 시 임베딩 삭제
        related_name='embedding'  # What: ChatMessage에서 임베딩 역참조
        # Why: 메시지-임베딩 1:1 매핑 보장
    )
    vector = models.JSONField(
        verbose_name='Embedding Vector'  # What: JSON 형태로 임베딩 벡터 저장
        # Why: 벡터 DB 대체 저장 또는 보조 용도로 활용
    )
    created_at = models.DateTimeField(
        auto_now_add=True  # What: 임베딩 생성 시각 자동 기록
        # Why: 생성 시점 분석 및 버전 관리
    )
'''



'''chat원본
    class ChatSession(models.Model):
    chat_session_id     = models.AutoField(primary_key=True, null=False, verbose_name="Chat Session ID")
    chat_session_title  = models.CharField(max_length=255, null=True, verbose_name="Chat Session Title")
    chat_session_info   = models.TextField(null=True, verbose_name="Chat Session Info")
    created_at          = models.DateTimeField(auto_now_add=True, null=False, verbose_name="Created At")
    updated_at          = models.DateTimeField(auto_now=True, null=False, verbose_name="Updated At")
    user                = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="User ID")

    def __str__(self):
        return self.chat_session_title
    class ChatMessage(models.Model):
    chat_message_id     = models.AutoField(primary_key=True, null=False, verbose_name="Chat Message ID")
    chat_order_number   = models.IntegerField(null=False, verbose_name="Chat Order Number")
    chat_sender         = models.CharField(max_length=10, null=False, verbose_name="Chat Sender")
    message             = models.TextField(null=True, verbose_name="Message")
    message_type        = models.CharField(max_length=10, null=False, verbose_name="Message Type")
    message_time        = models.DateTimeField(auto_now_add=True, null=False, verbose_name="Message Time")
    chat_session        = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=False, verbose_name="Chat Session ID")

    def __str__(self):
        return self.chat_sender + " - " + self.message[:50]
'''

class TourInfo(models.Model):
    tourinfo_id         = models.AutoField(primary_key=True, null=False, verbose_name="Content ID")
    title               = models.CharField(max_length=200, null=False, verbose_name="Title")
    content_type_id     = models.CharField(max_length=20, null=False, verbose_name="Content Type ID")
    address             = models.CharField(max_length=255, null=True, verbose_name="Address")
    lDongRegnCd         = models.CharField(max_length=20, null=False, verbose_name="Local Dong Code")
    lDongSignguCd       = models.CharField(max_length=20, null=False, verbose_name="Local Signgu Code")
    phone_number        = models.CharField(max_length=200, null=True, verbose_name="Phone Number")
    map_x               = models.FloatField(null=False, verbose_name="Map X")
    map_y               = models.FloatField(null=False, verbose_name="Map Y")
    category_one        = models.CharField(max_length=50, null=True, verbose_name="Category 1")
    category_two        = models.CharField(max_length=50, null=True, verbose_name="Category 2")
    category_three      = models.CharField(max_length=50, null=True, verbose_name="Category 3")
    content_id          = models.IntegerField(null=False, verbose_name="Content ID")

    def __str__(self):
        return self.title


class Restaurant(models.Model):
    restaurant_id        = models.AutoField(primary_key=True, null=False, verbose_name="Restaurant ID")
    store_name           = models.CharField(max_length=100, null=False, verbose_name="Store Name")
    category             = models.CharField(max_length=20, null=False, verbose_name="Category")
    description          = models.CharField(max_length=100, null=True, verbose_name="Description")
    address              = models.CharField(max_length=255, null=False, verbose_name="Address")
    phone_number         = models.CharField(max_length=20, null=True, verbose_name="Phone Number")
    rating               = models.FloatField(null=True, verbose_name="Rating")
    visitor_review_count = models.IntegerField(null=True, verbose_name="Visitor Review Count")
    blog_review_count    = models.IntegerField(null=True, verbose_name="Blog Review Count")
    monday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="monday_biz_hours")
    monday_break_time    = models.CharField(max_length=20, null=True, verbose_name="monday_break_time")
    monday_last_order    = models.CharField(max_length=20, null=True, verbose_name="monday_last_order")
    tuesday_biz_hours    = models.CharField(max_length=20, null=True, verbose_name="tuesday_biz_hours")
    tuesday_break_time   = models.CharField(max_length=20, null=True, verbose_name="tuesday_break_time")
    tuesday_last_order   = models.CharField(max_length=20, null=True, verbose_name="tuesday_last_order")
    wednesday_biz_hours  = models.CharField(max_length=20, null=True, verbose_name="wednesday_biz_hours")
    wednesday_break_time = models.CharField(max_length=20, null=True, verbose_name="wednesday_break_time")
    wednesday_last_order = models.CharField(max_length=20, null=True, verbose_name="wednesday_last_order")
    thursday_biz_hours   = models.CharField(max_length=20, null=True, verbose_name="thursday_biz_hours")
    thursday_break_time  = models.CharField(max_length=20, null=True, verbose_name="thursday_break_time")
    thursday_last_order  = models.CharField(max_length=20, null=True, verbose_name="thursday_last_order")
    friday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="friday_biz_hours")
    friday_break_time    = models.CharField(max_length=20, null=True, verbose_name="friday_break_time")
    friday_last_order    = models.CharField(max_length=20, null=True, verbose_name="friday_last_order")
    saturday_biz_hours   = models.CharField(max_length=20, null=True, verbose_name="saturday_biz_hours")
    saturday_break_time  = models.CharField(max_length=20, null=True, verbose_name="saturday_break_time")
    saturday_last_order  = models.CharField(max_length=20, null=True, verbose_name="saturday_last_order")
    sunday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="sunday_biz_hours")
    sunday_break_time    = models.CharField(max_length=20, null=True, verbose_name="sunday_break_time")
    sunday_last_order    = models.CharField(max_length=20, null=True, verbose_name="sunday_last_order")
    map_x                = models.FloatField(null=True, verbose_name="Map X")
    map_y                = models.FloatField(null=True, verbose_name="Map Y")

    def __str__(self):
        return self.store_name


class Accommodation(models.Model):
    accommodation_id    = models.AutoField(primary_key=True, null=False, verbose_name="Accommodation ID")
    store_name          = models.CharField(max_length=100, null=False, verbose_name="Store Name")
    grade               = models.CharField(max_length=50, null=False, verbose_name="Grade")
    address             = models.CharField(max_length=255, null=False, verbose_name="Address")
    phone_number        = models.CharField(max_length=20, null=True, verbose_name="Phone Number")
    rating              = models.FloatField(null=False, verbose_name="Rating")
    visitor_review_count= models.IntegerField(null=False, verbose_name="Visitor Review Count")
    blog_review_count   = models.IntegerField(null=False, verbose_name="Blog Review Count")
    reservation_site    = models.CharField(max_length=255, null=True, verbose_name="Reservation Site")
    map_x               = models.FloatField(null=True, verbose_name="Map X")
    map_y               = models.FloatField(null=True, verbose_name="Map Y")

    def __str__(self):
        return self.store_name
    

class Weather(models.Model):
    weather_id          = models.AutoField(primary_key=True, null=False, verbose_name="Weather ID")
    area_nm             = models.CharField(max_length=100, null=False, verbose_name="Area Name")
    base_date           = models.DateField(null=False, verbose_name="Base Date")
    pcp                 = models.IntegerField(null=False, verbose_name="Precipitation")
    pop                 = models.IntegerField(null=False, verbose_name="Probability of Precipitation")
    pty                 = models.IntegerField(null=False, verbose_name="Precipitation Type")
    reh                 = models.IntegerField(null=False, verbose_name="Relative Humidity")
    sno                 = models.IntegerField(null=False, verbose_name="Snowfall")
    sky                 = models.IntegerField(null=False, verbose_name="Sky Condition")
    tmp                 = models.FloatField(null=False, verbose_name="Temperature")
    tmn                 = models.FloatField(null=False, verbose_name="Minimum Temperature")
    tmx                 = models.FloatField(null=False, verbose_name="Maximum Temperature")
    wsd                 = models.IntegerField(null=False, verbose_name="Wind Direction")
    base_time           = models.TimeField(null=False, verbose_name="Base Time")
    fcst_date           = models.DateField(null=False, verbose_name="Forecast Data")
    fcst_time           = models.TimeField(null=False, verbose_name="Forecast Time")
    nx                  = models.IntegerField(null=False, verbose_name="NX")
    ny                  = models.IntegerField(null=False, verbose_name="NY")
    map_x               = models.FloatField(null=True, verbose_name="Map X")
    map_y               = models.FloatField(null=True, verbose_name="Map Y")
    

    def __str__(self):
        return self.area_nm
    

class CongestionData(models.Model):
    congestion_data_id  = models.AutoField(primary_key=True, null=False, verbose_name="Congestion Data ID")
    area_cd             = models.CharField(max_length=20, null=False, verbose_name="Area Code")
    area_nm             = models.CharField(max_length=100, null=False, verbose_name="Area Name")
    base_date           = models.DateField(null=False, verbose_name="Base Date")
    area_congest_lvl    = models.CharField(max_length=20, null=False, verbose_name="Area Congestion Level")
    area_congest_msg    = models.TextField(null=False, verbose_name="Area Congestion Message")
    area_ppltn_min      = models.IntegerField(null=False, verbose_name="Area Population Min")
    area_ppltn_max      = models.IntegerField(null=False, verbose_name="Area Population Max")
    male_ppltn_rate     = models.FloatField(null=False, verbose_name="male_ppltn_rate")
    female_ppltn_rate   = models.FloatField(null=False, verbose_name="female_ppltn_rate")
    ppltn_rate_0        = models.FloatField(null=False, verbose_name="Population Rate 0")
    ppltn_rate_10       = models.FloatField(null=False, verbose_name="Population Rate 10")
    ppltn_rate_20       = models.FloatField(null=False, verbose_name="Population Rate 20")
    ppltn_rate_30       = models.FloatField(null=False, verbose_name="Population Rate 30")
    ppltn_rate_40       = models.FloatField(null=False, verbose_name="Population Rate 40")
    ppltn_rate_50       = models.FloatField(null=False, verbose_name="Population Rate 50")
    ppltn_rate_60       = models.FloatField(null=False, verbose_name="Population Rate 60")
    ppltn_rate_70       = models.FloatField(null=False, verbose_name="Population Rate 70")
    resnt_ppltn_rate    = models.FloatField(null=False, verbose_name="Resident Population Rate")
    non_resnt_ppltn_rate= models.FloatField(null=False, verbose_name="Non-Resident Population Rate")
    replace_yn          = models.CharField(max_length=2, null=False, verbose_name="Replace YN")
    fcst_yn             = models.CharField(max_length=2, null=False, verbose_name="Forecast YN")
    fcst_congest_lvl    = models.CharField(max_length=20, null=True, verbose_name="Forecast Congestion Level")
    fcst_ppltn_min      = models.IntegerField(null=True, verbose_name="Forecast Population Min")
    fcst_ppltn_max      = models.IntegerField(null=True, verbose_name="Forecast Population Max")
    base_time           = models.TimeField(null=False, verbose_name="Base Time")
    fcst_date           = models.DateTimeField(null=True, verbose_name="Forecast Time")
    fcst_time           = models.TimeField(null=True, verbose_name="Forecast Time")
    map_x               = models.FloatField(null=True, verbose_name="Map X")
    map_y               = models.FloatField(null=True, verbose_name="Map Y")
    address             = models.CharField(max_length=255, null=True, verbose_name="Address")

    def __str__(self):
        return self.area_nm
    

        