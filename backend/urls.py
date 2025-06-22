# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # DRF API의 URL을 포함시킵니다.
    # '/api/' 경로로 들어오는 모든 요청은 api 앱의 urls.py로 라우팅됩니다.
    path('api/', include('api.urls')),
]