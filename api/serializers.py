from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from users.models import User
from django.contrib.auth.models import Group

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    group = serializers.CharField(write_only=True)  # New field for group

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'confirm_password',
                 'first_name', 'last_name', 'phone_number', 'gender', 'group')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'group': {'required': True}
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

        # Group validation
        group_name = data['group'].lower()
        available_groups = list(Group.objects.values_list('name', flat=True))
        
        if not available_groups:
            raise serializers.ValidationError("No groups are defined in the system")
        
        if group_name not in [group.lower() for group in available_groups]:
            raise serializers.ValidationError({
                "group": f"Invalid group. Available groups are: {', '.join(available_groups)}"
            })

        # Store the actual Group object
        data['group'] = Group.objects.get(name__iexact=group_name)
        
        return data

    def create(self, validated_data):
        group = validated_data.pop('group')  # Remove group from validated_data
        user = User.objects.create_user(**validated_data)
        user.groups.add(group)  # Add user to the group
        return user

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
        read_only_fields = ('id', 'email', 'username', 'date_joined', 'last_login')

    def validate(self, data):
        # Check if any read-only field is being attempted to modify
        read_only_attempts = []
        request_data = dict(self.context['request'].data)
        
        for field in self.Meta.read_only_fields:
            if field in request_data:
                read_only_attempts.append(field)
        
        if read_only_attempts:
            raise serializers.ValidationError({
                'error': f'Cannot modify read-only field(s): {", ".join(read_only_attempts)}',
                'read_only_fields': self.Meta.read_only_fields
            })
        
        return data
    
class PasswordResetSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match")
        
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError("Current password is incorrect")
            
        return data