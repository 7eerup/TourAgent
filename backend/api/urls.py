from django.urls import path
from .views import CommonPlaceView, RegisterAPIView, LoginView, LogoutAPIView, TokenVerifyAPIView,  CookieLoginView, CookieRefreshView, MapView, FeedbackAPI

from rest_framework_simplejwt.views import TokenRefreshView

#==============chat====================
from django.urls import include                            # what: include 함수 임포트 why: 하위 URL 연결
from rest_framework.routers import DefaultRouter                # what: DRF 라우터 임포트 why: 자동 라우팅
from api.viewsets import ChatMessageViewSet, ChatSessionViewSet # what: ViewSet 임포트 why: 라우터 등록 대상

from .views import ChatSessionStartAPIView, ChatSessionMessageAPIView, RealtimeMapView, ChatSessionStartAPIView2

urlpatterns = [
    path('v1/users/<int:user_pk>/chat-sessions/start/', ChatSessionStartAPIView.as_view(), name='session-start-api'),
    path('v1/users/<int:user_pk>/chat-sessions/start2/<int:session_pk>/', ChatSessionStartAPIView2.as_view(), name='session-start2-api'),
    path('v1/users/<int:user_pk>/chat-sessions/<int:session_id>/send-messages/', ChatSessionMessageAPIView.as_view(), name='message-send-api'),
    path('v1/users/', RegisterAPIView.as_view(), name='users'),
    # path("v1/login/", CookieLoginView.as_view()),
    path('v1/login/', LoginView.as_view()),
    path('v1/users/<int:user_pk>/token/verify/', TokenVerifyAPIView.as_view()),
    path('v1/users/<int:user_pk>/token/refresh/', CookieRefreshView.as_view()),
    path('v1/users/<int:user_pk>/token/logout/', LogoutAPIView.as_view()),
    # 테스트용
    path('v1/map-test/', MapView.as_view()), #맵 테스트용 api
    path('v1/maps/current-location/', RealtimeMapView.as_view(), name='realtime-map'),  # 실시간 지도 API
    path('v1/maps/common-places/', CommonPlaceView.as_view(), name='common-places'),    # 일반 장소 API
    
    # 피드백
    path('v1/users/<int:user_pk>/chat-sessions/<int:session_id>/feedbacks/', FeedbackAPI.as_view(), name='feedback'),
]


router = DefaultRouter()                                        # what: 라우터 인스턴스 생성 why: 자동 URL 매핑 준비
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions',
    ChatSessionViewSet,
    basename='user-chat-sessions'
)

# 챗 세션 CRUD
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions/(?P<session_pk>\d+)/messages',
    ChatMessageViewSet,
    basename='session-messages'
)



from .viewsets import (                                                  # ViewSet 임포트
    ChatComponentViewSet,
    ChatInteractionViewSet,
    ChatSessionSummaryViewSet,
    MessageEmbeddingViewSet,
)

# 신규: 각 테이블별 CRUD 엔드포인트  
# 특정 메시지의 컴포넌트
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions/(?P<session_pk>\d+)/messages/(?P<message_pk>\d+)/components',
    ChatComponentViewSet,
    basename='message-components'
)

# 특정 메시지의 인터랙션
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions/(?P<session_pk>\d+)/messages/(?P<message_pk>\d+)/interactions',
    ChatInteractionViewSet,
    basename='message-interactions'
)

# 세션 요약
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions/(?P<session_pk>\d+)/summaries',
    ChatSessionSummaryViewSet,
    basename='session-summaries'
)

# 특정 메시지의 임베딩
router.register(
    r'users/(?P<user_pk>\d+)/chat-sessions/(?P<session_pk>\d+)/messages/(?P<message_pk>\d+)/embeddings',
    MessageEmbeddingViewSet,
    basename='message-embeddings'
)

urlpatterns += [
    path('v1/', include(router.urls)),                         # what: 라우터가 생성한 URL 포함 why: API 엔드포인트 일괄 등록
]