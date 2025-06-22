from django.db import transaction                               # DB 트랜잭션 관리용
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from .models import Feedback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from math import radians, cos, sin, asin, sqrt
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, FeedbackSerializer

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError

from django.contrib.auth import get_user_model

'''
class LoginAPIView(TokenObtainPairView):
    """
    POST /api/login/
    {
      "username": "your_username",
      "password": "your_password"
    }
    → { "token": "abcdefgh12345678" }
    이후 요청의 헤더에:
    Authorization: Token abcdefgh12345678
    형태로 토큰을 보내면 인증됩니다.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
'''

# 실제 사용할 User 모델 참조
User = get_user_model()                                           # AbstractBaseUser 상속 커스텀 모델 지원

class LoginView(APIView):
    authentication_classes = []                                   # 뷰 차원에서 인증 로직 제거 → 완전 stateless
    permission_classes = []                                       # 뷰 차원에서 권한 검사 제거 → 누구나 접근 가능

    def post(self, request):
        # 1) 요청 body에서 email과 password 추출
        email = request.data.get('email')                         # 클라이언트가 보낸 이메일
        password = request.data.get('password')                   # 클라이언트가 보낸 비밀번호

        # 2) 해당 이메일로 User 인스턴스 조회 시도
        try:
            user = User.objects.get(email=email)                  # email 필드로 한 건 검색
        except User.DoesNotExist:
            # 3a) 사용자가 없으면 인증 실패
            return Response(
                {'detail': '이메일 또는 비밀번호 오류'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 4) 비밀번호 검증 (해시 비교)
        if not user.check_password(password):                      # 저장된 해시와 비교
            # 4a) 비밀번호가 틀리면 인증 실패
            return Response(
                {'detail': '이메일 또는 비밀번호 오류'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 5) 인증 성공 시 id와 username 반환
        return Response(
            {'id': user.id, 'username': user.username},
            status=status.HTTP_200_OK
        )


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
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # access/refresh
        data = response.data
        refresh = data.pop("refresh")          # 쿠키로 이동
        access  = data.pop("access")           # 그대로 body 또는 헤더

        # HttpOnly 쿠키 설정
        response.set_cookie(
            "refresh_token",
            refresh,
            httponly=True,
            # secure=True,
            secure=False,         
            # samesite="Lax",
            samesite="None",
            path='/',
            max_age=60*60*24*7,
        )
        # 선택: access 도 쿠키로
        response.set_cookie(
            "access_token",
            access,
            httponly=False,       # JS 읽어서 Authorization 헤더에 실어도 OK
            # secure=True,
            secure=False,
            # samesite="Lax",
            samesite="None",
            path='/',
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

'''
class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # 블랙리스트에 등록
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
'''

#===채팅 테이블 관련 기본 CRUD는 뷰셋에 있고, 여기에는 커스텀 API 구현이 여기에 들어갑니다===
from .models import ChatSession, ChatMessage                              # 사용하는 모델 임포트
from .serializers import ChatSessionSerializer, ChatMessageSerializer     # 직렬화기 임포트
from .services.llm_service import DummyLLMService, ss_LLMService          # 더미 LLM 서비스 구현체 import

from .models import ChatInteraction, ChatComponent
from .services.teamdb_langgraph_v5 import get_result

def _save_and_parse_deltas(message, deltas):
    """
    ChatInteraction 및 ChatComponent 저장 헬퍼
    메시지당 하나의 ChatInteraction만 update_or_create 사용
    """
    # 첫 번째 텍스트 델타를 interaction으로 기록
    text_delta = next((d for d in deltas if d.get('type') == 'text'), None)
    if text_delta:
        ChatInteraction.objects.update_or_create(
            chatmessage=message,
            defaults={
                'request': {},
                'response': text_delta.get('payload', {})
            }
        )
    # UI 컴포넌트들 기록
    for idx, delta in enumerate(deltas):
        if delta.get('type') in ('map_marker', 'form', 'image_carousel', 'button'):
            ChatComponent.objects.create(
                chatmessage=message,
                component_type=delta['type'],
                payload=delta.get('payload', {}),
                order=idx
            )

class ChatSessionStartAPIView(APIView):
    '''
        permission_classes = [permissions.IsAuthenticated]  # 인증된 요청만 허용
        authentication_classes = [CookieJWTAuthentication]  # 쿠키 기반 인증
    '''
    def post(self, request, user_pk):
        # # 1) 인증 및 사용자 검증
        # if request.user.pk != user_pk:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # 2) 사용자 메시지 및 파라미터
        # user_msg = request.data.get('message') #유저 메시지가 없어진 버전
        params   = request.data.get('session_parameters', {})
        session_params = request.data.get("session_parameters")

        llm = ss_LLMService()
        # 3) 세션정보 생성 LLM 호출 -> session DB에 저장
        title, info = llm.generate_session_metadata(session_parameters=params)
        with transaction.atomic():
            session = ChatSession.objects.create(user_id=user_pk, title=title, info=info, parameters=params)
            user_message = ChatMessage.objects.create(chatsession=session, order=0, sender='user', content=info)


        return Response(
            {
                "session": ChatSessionSerializer(session).data
            },
            status=status.HTTP_201_CREATED,
        )

        # # 6) 직렬화 및 델타 응답 조립) 응답
        # return Response({
        #     'session': ChatSessionSerializer(session).data,
        #     'messages': [ChatMessageSerializer(bot_message).data],
        # }, status=status.HTTP_201_CREATED)
        
        
class ChatSessionStartAPIView2(APIView):
    '''
        permission_classes = [permissions.IsAuthenticated]  # 인증된 요청만 허용
        authentication_classes = [CookieJWTAuthentication]  # 쿠키 기반 인증
    '''
    def post(self, request, user_pk, session_pk):
        # # 1) 인증 및 사용자 검증
        # if request.user.pk != user_pk:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        # 2) 사용자 메시지 및 파라미터
        # user_msg = request.data.get('message') #유저 메시지가 없어진 버전
        params   = request.data.get('session_parameters', {})
        session_params = request.data.get("session_parameters")
        session = ChatSession.objects.get(id=session_pk)

        llm_answer, llm_places = get_result(session_parameters = session_params)
        # full_text = ''.join(d.get('payload',{}).get('content','') for d in deltas if d.get('type') == 'text')               
        # 5) 봇 메시지 저장 및 델타 처리
        with transaction.atomic():
            bot_message = ChatMessage.objects.create(
                chatsession=session,
                order=1,
                sender='assistant',
                content=llm_answer
            )
            # 델타별 기록 헬퍼 호출
            # _save_and_parse_deltas(bot_message, deltas)
            for idx, place in enumerate(llm_places):
                ChatComponent.objects.create(
                    chatmessage=bot_message,
                    component_type='place',  # 컴포넌트 유형을 명시적으로 기록
                    payload=place,           # JSONField에 dict 형태로 저장
                    order=idx                # 순서 지정
            )
                
            components_qs = ChatComponent.objects.filter(
                chatmessage=bot_message, component_type="place"
            ).order_by("order")

            places = [comp.payload for comp in components_qs]

        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "messages": [ChatMessageSerializer(bot_message).data],
                "places": places,
            },
            status=status.HTTP_201_CREATED,
        )

        # # 6) 직렬화 및 델타 응답 조립) 응답
        # return Response({
        #     'session': ChatSessionSerializer(session).data,
        #     'messages': [ChatMessageSerializer(bot_message).data],
        # }, status=status.HTTP_201_CREATED)


class ChatSessionMessageAPIView(APIView):

    '''
        permission_classes = [permissions.IsAuthenticated]
    '''
    def post(self, request, user_pk, session_id):
        # 1) 인증 및 세션 검증
        if request.user.pk != user_pk:
            return Response(status=status.HTTP_403_FORBIDDEN)
        session = get_object_or_404(ChatSession, id=session_id, user_id=user_pk)

        # 2) 사용자 메시지 저장
        user_msg = request.data.get('message')
        with transaction.atomic():
            count = ChatMessage.objects.filter(chatsession=session).count()
            user_message = ChatMessage.objects.create(chatsession=session, order=count, sender='user', content=user_msg)

        # 3) 델타 생성 및 조합
        deltas = DummyLLMService().generate_bot_response(session_id=session.id, messages=[{'sender':'user','content':user_msg}], **session.parameters)
        full_text = ''.join(d.get('payload',{}).get('content','') for d in deltas if d.get('type')=='text')

        # 4) 봇 메시지 저장 및 델타 처리
        with transaction.atomic():
            bot_message = ChatMessage.objects.create(chatsession=session, order=user_message.order+1, sender='assistant', content=full_text)
            _save_and_parse_deltas(bot_message, deltas)

        # 5) 응답
        return Response({'messages': [ChatMessageSerializer(user_message).data, ChatMessageSerializer(bot_message).data], 'deltas': deltas}, status=status.HTTP_200_OK)
    

class MapView(APIView):
    def get(self, request):
        if(request):
            pass
        else:
            pass


def haversine(lat1, lng1, lat2, lng2):
    R = 6371  # 지구 반지름 (km)
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(a))

class RealtimeMapView(APIView):
    def get(self, request):
        try:
            lat = float(request.query_params.get('lat')) if request.query_params.get('lat') else None
            lng = float(request.query_params.get('lng')) if request.query_params.get('lng') else None
            radius = float(request.query_params.get('radius', 5))
        except ValueError:
            return Response({"detail": "lat, lng, radius 파라미터는 숫자여야 합니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        places_data = [
            {"name": "서울역",   "map_x": 37.5547, "map_y": 126.9706, "description": "아름다운 서울역"},
            {"name": "시청역",   "map_x": 37.5658, "map_y": 126.9752, "description": "광장이 인상적인 시청역"},
            {"name": "강남역",   "map_x": 37.4979, "map_y": 127.0276, "description": "분주한 강남역"},
            {"name": "건대입구", "map_x": 37.5407, "map_y": 127.0703, "description": "학생들로 붐비는 건대입구"},
            {"name": "홍대입구", "map_x": 37.5563, "map_y": 126.9236, "description": "예술의 거리 홍대입구"},
            {"name": "합정역",   "map_x": 37.5500, "map_y": 126.9147, "description": "교통 요지 합정역"}
        ]

        if lat is not None and lng is not None:
            places_data = [
                p for p in places_data
                if haversine(lat, lng, p["map_x"], p["map_y"]) <= radius
            ]

        return Response({"places": places_data}, status=status.HTTP_200_OK)
    

class CommonPlaceView(APIView):
    def get(self, request):
        try:
            lat = float(request.query_params.get('lat')) if request.query_params.get('lat') else None
            lng = float(request.query_params.get('lng')) if request.query_params.get('lng') else None
            radius = float(request.query_params.get('radius', 3))  # 일반 장소는 기본 3km
        except ValueError:
            return Response({"detail": "lat, lng, radius 파라미터는 숫자여야 합니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        common_places_data = [
            {"name": "이마트24 합정점", "map_x": 37.5499, "map_y": 126.9140, "description": "편의점"},
            {"name": "북스쿠터 독립서점", "map_x": 37.5759, "map_y": 126.9883, "description": "90년대 만화·독립출판 전문 서점"},
            {"name": "연남동 조용한 양조장", "map_x": 37.5642, "map_y": 126.9220, "description": "소규모 수제 맥주 탭룸, 간판 없음"},
            {"name": "카페 의외의공간", "map_x": 37.5507, "map_y": 126.9351, "description": "주택가 골목 깊숙이 숨은 로스터리 카페"},
            {"name": "가산디지털단지 제1공장", "map_x": 37.4770, "map_y": 126.8890, "description": "전자부품 조립 전문 중소공장"},
            {"name": "가산디지털단지 제2공장",   "map_x": 37.4772, "map_y": 126.8894, "description": "전자부품 조립 전문 중소공장"},
            {"name": "구로디지털 물류센터",     "map_x": 37.4856, "map_y": 126.9011, "description": "IT장비 보관 전용 자동화 창고"},
            {"name": "남양주 화도산업단지 입구", "map_x": 37.6547, "map_y": 127.3159, "description": "산단 출입 차량 통제 게이트"},
            {"name": "남양주 화도산업단지 A동", "map_x": 37.6550, "map_y": 127.3165, "description": "대량생산형 조립 제조시설"},
            {"name": "문래 창작촌 파이 공방", "map_x": 37.5149, "map_y": 126.8943, "description": "금속공예가들이 직접 운영하는 디저트·공예 복합 공간"},
            {"name": "선린상가 지하갤러리", "map_x": 37.5662, "map_y": 126.9654, "description": "빈티지 건물 지하에 있는 실험예술 전시장"},
            
        ]

        if lat is not None and lng is not None:
            common_places_data = [
                p for p in common_places_data
                if haversine(lat, lng, p["map_x"], p["map_y"]) <= radius
            ]

        return Response({"common_places": common_places_data}, status=status.HTTP_200_OK)


class FeedbackAPI(APIView):

    def post(self, request, user_pk, session_id):
        from django.shortcuts import get_object_or_404
        from .models import ChatSession

        # URL로 전달된 user와 session 확인
        session = get_object_or_404(ChatSession, id=session_id, user_id=user_pk)
        
        # 실제 serializer에는 session 객체로 전달
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(session=session)
        result="성공"
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request, user_pk, session_id):
        # 1. 해당 세션이 사용자에게 속해있는지 검증
        session = get_object_or_404(ChatSession, id=session_id, user_id=user_pk)

        # 2. 해당 세션에 대한 피드백 모두 조회
        feedbacks = Feedback.objects.filter(session=session)

        # 3. 직렬화: many=True 설정 필수!
        serializer = FeedbackSerializer(feedbacks, many=True)

        # 4. 응답
        return Response(serializer.data, status=status.HTTP_200_OK)



