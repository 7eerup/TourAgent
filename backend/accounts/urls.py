from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # 로그인
    path("login/", views.login, name="login"),
    
    # 추가
    path('add/', views.add, name='add'),
     
]
