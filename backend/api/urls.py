from django.urls import path

from . import views

urlpatterns = [
    # 메인

    # 조회
    path('', views.list, name='list'),

    # 로그인
    path("login/", views.login, name="login"),
    path("login/auth/", views.login_auth, name="login_auth"),
    
    # 추가
    path('add/', views.add, name='add'),
    # 저장
    path('add/save/', views.add_save, name='add_save'),
    # 수정
    path("update/<int:idx>/", views.update, name="update"),
    path("update/save/", views.update_save, name="update_save"),
    #삭제
    path("delete/<int:id>/", views.delete, name="delete"),
     
]
