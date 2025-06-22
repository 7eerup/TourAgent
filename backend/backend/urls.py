from django.contrib import admin
from django.urls import path, include


# URL 라우팅 설정
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
