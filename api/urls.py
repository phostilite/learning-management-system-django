from django.urls import path
from .views import LoginAPIView, SignupAPIView, UserDetailAPIView

app_name = 'api'

urlpatterns = [
    path('auth/signup/', SignupAPIView.as_view(), name='api_signup'),
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('user/me/', UserDetailAPIView.as_view(), name='api_user_detail'),
]
