from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from .auth_serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from .models import EmailVerification


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user (inactive until email verified)"""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create user as inactive
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                is_active=False  # User must verify email first
            )
            
            # Create verification code
            code = EmailVerification.generate_code()
            EmailVerification.objects.create(user=user, code=code)
            
            # Send verification email
            send_mail(
                subject='Verify your email - QR Generator',
                message=f'Your verification code is: {code}\n\nThis code expires in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Registration successful. Please check your email for verification code.',
                'email': user.email,
                'requires_verification': True
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            return Response({
                'error': 'Username or email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email with code"""
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not email or not code:
        return Response({
            'error': 'Email and code are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        verification = EmailVerification.objects.get(user=user)
        
        if verification.is_expired():
            return Response({
                'error': 'Verification code has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if verification.code != code:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate user
        user.is_active = True
        user.save()
        
        # Delete verification record
        verification.delete()
        
        # Create token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Email verified successfully',
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    except EmailVerification.DoesNotExist:
        return Response({
            'error': 'No pending verification for this email'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """Resend verification code"""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email, is_active=False)
        
        # Delete old verification and create new one
        EmailVerification.objects.filter(user=user).delete()
        code = EmailVerification.generate_code()
        EmailVerification.objects.create(user=user, code=code)
        
        # Send new code
        send_mail(
            subject='Verify your email - QR Generator',
            message=f'Your new verification code is: {code}\n\nThis code expires in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Verification code sent'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'No pending verification for this email'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user and return token"""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user:
            if user.is_active:
                # Login user (for session-based auth)
                login(request, user)
                
                # Get or create token
                token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'token': token.key
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Account is disabled'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_user(request):
    """Logout user and delete token"""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        
        # Logout user (for session-based auth)
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Error during logout'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile(request):
    """Get current user profile"""
    return Response({
        'user': UserSerializer(request.user).data
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_profile(request):
    """Update user profile"""
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_username(request):
    """Check if username is available"""
    username = request.data.get('username', '')
    
    if not username:
        return Response({
            'error': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(username=username).exists()
    
    return Response({
        'available': not exists,
        'message': 'Username is available' if not exists else 'Username is already taken'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email(request):
    """Check if email is available"""
    email = request.data.get('email', '')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(email=email).exists()
    
    return Response({
        'available': not exists,
        'message': 'Email is available' if not exists else 'Email is already registered'
    }, status=status.HTTP_200_OK)