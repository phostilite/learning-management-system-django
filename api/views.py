from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from .serializers import LoginSerializer, SignupSerializer, UserDetailSerializer, PasswordResetSerializer
import logging
from rest_framework.permissions import IsAuthenticated
from .utils import BearerTokenAuthentication


logger = logging.getLogger(__name__)

class SignupAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        try:
            if serializer.is_valid():
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                
                response_data = {
                    'status': 'success',
                    'message': 'User registered successfully',
                    'data': {
                        'token': token.key,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'group': user.groups.first().name if user.groups.exists() else None
                        }
                    }
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response({
                'status': 'error',
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in signup: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred during registration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        try:
            if serializer.is_valid():
                user = serializer.validated_data['user']
                login(request, user)
                token, _ = Token.objects.get_or_create(user=user)

                response_data = {
                    'status': 'success',
                    'message': 'Login successful',
                    'data': {
                        'token': token.key,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'timezone': user.timezone,
                            'preferred_language': user.preferred_language
                        }
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)

            return Response({
                'status': 'error',
                'message': 'Invalid credentials',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in login: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred during login'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailAPIView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            serializer = UserDetailSerializer(request.user)
            response_data = {
                'status': 'success',
                'message': 'User data retrieved successfully',
                'data': serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching user data: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while fetching user data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request):
        try:
            serializer = UserDetailSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                response_data = {
                    'status': 'success',
                    'message': 'User profile updated successfully',
                    'data': serializer.data
                }
                return Response(response_data, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating user data: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while updating user data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            user = request.user
            # Soft delete - deactivate user
            user.is_active = False
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'User account deactivated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while deactivating user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PasswordResetAPIView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = PasswordResetSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                user = request.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Optionally invalidate old token and generate new one
                Token.objects.filter(user=user).delete()
                new_token = Token.objects.create(user=user)
                
                return Response({
                    'status': 'success',
                    'message': 'Password updated successfully',
                    'data': {
                        'token': new_token.key  # Return new token
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in password reset: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An error occurred while resetting password'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)