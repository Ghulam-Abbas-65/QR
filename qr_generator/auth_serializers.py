from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""
    username = serializers.CharField(
        max_length=150,
        min_length=3,
        help_text="Username must be 3-150 characters long"
    )
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    def validate_username(self, value):
        """Validate username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        
        # Check for valid characters
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        
        return value
    
    def validate_email(self, value):
        """Validate email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_password(self, value):
        """Validate password using Django's built-in validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return attrs


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate_username(self, value):
        """Allow login with username or email"""
        return value.strip()


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        """Validate new password"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return attrs