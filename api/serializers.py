from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from users.models import User

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'confirm_password', 
                 'first_name', 'last_name', 'phone_number', 'gender')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        
        # Email validation
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered")
        
        # Username validation
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already taken")
        
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not (email or username):
            raise serializers.ValidationError("Either email or username is required")

        # Try to authenticate with email if provided
        if email:
            try:
                username = User.objects.get(email=email).username
            except User.DoesNotExist:
                raise serializers.ValidationError("No account found with this email")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data['user'] = user
        return data

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'gender', 'picture', 'timezone',
            'bio', 'preferred_language', 'email_notifications_enabled',
            'sms_notifications_enabled', 'date_joined', 'last_login'
        )
        read_only_fields = fields