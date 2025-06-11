from django.urls import path
from .views import UserListCreateAPIView, UserRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('user/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('user/<int:user_id>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user-detail'),
]
