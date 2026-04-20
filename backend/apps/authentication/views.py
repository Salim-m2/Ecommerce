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