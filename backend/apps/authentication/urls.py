# apps/authentication/urls.py

from django.urls import path
from apps.authentication.views import (
    RegisterView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    MeView,
)

urlpatterns = [
    # Account creation
    path('register/', RegisterView.as_view(), name='auth-register'),

    # Login — sets httpOnly JWT cookies
    path('login/', LoginView.as_view(), name='auth-login'),

    # Silent token refresh — reads refresh cookie, issues new access cookie
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),

    # Logout — clears both cookies
    path('logout/', LogoutView.as_view(), name='auth-logout'),

    # Returns current user data — used on page reload in React
    path('me/', MeView.as_view(), name='auth-me'),
]