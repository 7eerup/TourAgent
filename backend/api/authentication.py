# api/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class CookieJWTAuthentication(JWTAuthentication):
    """
    HTTPOnly 쿠키에서 'access_token' 값을 꺼내
    simplejwt의 토큰 검증 로직에 넘겨 주는 인증 클래스.
    CSRF 검증은 생략(enforce_csrf override).
    """

    def authenticate(self, request):
        # 1) request.COOKIES에서 토큰 꺼내기
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None  # 쿠키에 토큰 없으면 인증 시도도 하지 않음

        # 2) 토큰 검증 및 유저 조회
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return (user, validated_token)

    def enforce_csrf(self, request):
        """
        CSRF 검증을 완전히 스킵.
        쿠키만 있는 상태에서 API 호출을 허용하기 위함.
        """
        return  # 아무 동작도 하지 않음