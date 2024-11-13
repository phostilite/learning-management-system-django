from django.urls import path
from .views import LoginAPIView, SignupAPIView, UserDetailAPIView, PasswordResetAPIView

app_name = 'api'

urlpatterns = [
    path('auth/signup/', SignupAPIView.as_view(), name='api_signup'),
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('user/me/', UserDetailAPIView.as_view(), name='api_user_detail'),
    path('password/reset/', PasswordResetAPIView.as_view(), name='password-reset'),
]
