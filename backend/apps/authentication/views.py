from django.shortcuts import render

# Create your views here.
# apps/authentication/views.py

from datetime import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.authentication.documents import Token
from apps.users.documents import User
from apps.authentication.backends import MongoAuthBackend
from apps.authentication.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
)
from apps.authentication.utils import (
    get_tokens_for_user,
    set_auth_cookies,
    clear_auth_cookies,
)
from apps.users.documents import User


# ─────────────────────────────────────────────
# CUSTOM THROTTLE FOR LOGIN
# Tighter limit — 10 attempts per minute max
# Prevents brute force attacks on the login endpoint
# ─────────────────────────────────────────────
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


# ─────────────────────────────────────────────
# REGISTER VIEW
# POST /api/v1/auth/register/
# ─────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # Create the user document
        user = User(
            email      = data['email'],
            first_name = data['first_name'],
            last_name  = data['last_name'],
        )

        # Hash and store the password — never store raw
        user.set_password(data['password'])
        user.save()

        return Response(
            {
                'message': 'Account created successfully. Please log in.',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────
# LOGIN VIEW
# POST /api/v1/auth/login/
# ─────────────────────────────────────────────
class LoginView(APIView):
    permission_classes  = [AllowAny]
    throttle_classes    = [LoginRateThrottle]   # 10 attempts/minute

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # Verify credentials against MongoDB via our custom backend
        backend = MongoAuthBackend()
        user = backend.authenticate(
            request,
            email    = data['email'],
            password = data['password'],
        )

        if user is None:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        user.save()

        # Generate JWT token pair
        tokens = get_tokens_for_user(user)

        # Build the response
        response = Response(
            {
                'message': 'Login successful.',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )

        # Attach both tokens as httpOnly cookies
        set_auth_cookies(
            response,
            access_token  = tokens['access'],
            refresh_token = tokens['refresh'],
        )

        return response


# ─────────────────────────────────────────────
# TOKEN REFRESH VIEW
# POST /api/v1/auth/token/refresh/
# Reads the refresh cookie and issues a new access cookie
# ─────────────────────────────────────────────
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Read refresh token from httpOnly cookie
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)

        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found. Please log in again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Validate the refresh token
            token = RefreshToken(refresh_token)

            # Generate a new access token from the refresh token
            new_access_token = str(token.access_token)

        except TokenError:
            return Response(
                {'error': 'Refresh token is invalid or expired. Please log in again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response(
            {'message': 'Token refreshed successfully.'},
            status=status.HTTP_200_OK
        )

        # Set the new access cookie — refresh cookie stays the same
        response.set_cookie(
            key      = settings.JWT_AUTH_COOKIE,
            value    = new_access_token,
            max_age  = 60 * 15,             # 15 minutes
            httponly = True,
            secure   = getattr(settings, 'JWT_AUTH_COOKIE_SECURE', False),
            samesite = getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
        )

        return response


# ─────────────────────────────────────────────
# LOGOUT VIEW
# POST /api/v1/auth/logout/
# Clears both cookies — user is immediately logged out
# ─────────────────────────────────────────────
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK
        )

        # Delete both JWT cookies from the browser
        clear_auth_cookies(response)

        return response


# ─────────────────────────────────────────────
# ME VIEW
# GET /api/v1/auth/me/
# Returns the currently authenticated user's data.
# Used on page refresh to restore auth state in React.
# ─────────────────────────────────────────────
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user is already the full mongoengine User document
        # set by MongoJWTAuthentication
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK
        )
    
# ─────────────────────────────────────────────
# PASSWORD RESET REQUEST VIEW
# POST /api/v1/auth/password/reset/
#
# Accepts an email address, creates a Token
# document, and would send a reset email.
# Email sending is wired up in Week 8.
# ─────────────────────────────────────────────
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Always return the same response whether or not the email exists
        # This prevents user enumeration attacks — an attacker shouldn't
        # be able to tell which emails are registered by trying this endpoint
        try:
            user = User.objects.get(email=email)
            # Generate a secure token valid for 1 hour
            plain_token = Token.create_for_user(
                user,
                token_type='password_reset',
                hours_valid=1,
            )
            # TODO Week 8: send_password_reset_email.delay(user.id, plain_token)
            # For now, print to console so we can test manually
            print(f"\n[DEV ONLY] Password reset token for {email}: {plain_token}\n")

        except User.DoesNotExist:
            # Do nothing — but don't reveal that the email doesn't exist
            pass

        return Response(
            {'detail': 'If this email exists, a reset link will be sent.'},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────
# PASSWORD RESET CONFIRM VIEW
# POST /api/v1/auth/password/reset/confirm/
#
# Accepts the plain token + new password.
# Verifies the token, updates the password,
# deletes the token so it can't be reused.
# ─────────────────────────────────────────────
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        plain_token  = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '').strip()

        # Validate inputs
        if not plain_token:
            return Response(
                {'error': 'Reset token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_password or len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the token — returns Token document or None
        token_doc = Token.verify_token(plain_token, token_type='password_reset')

        if token_doc is None:
            return Response(
                {'error': 'Reset token is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look up the user
        try:
            user = User.objects.get(id=token_doc.user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update the password securely
        user.set_password(new_password)
        user.save()

        # Delete the token so it cannot be reused
        token_doc.delete()

        return Response(
            {'detail': 'Password has been reset successfully. Please log in.'},
            status=status.HTTP_200_OK
        )