from django.contrib import admin
from django.urls import path, include

# URL 라우팅 설정
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # 사용자 로그인 인증 URL
    path('chatgpt/', include('chatgpt.urls')),  # chatgpt URL
]
