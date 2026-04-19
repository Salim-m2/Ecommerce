# apps/authentication/utils.py

from datetime import datetime
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


# ─────────────────────────────────────────────
# GENERATE TOKENS FOR A USER
#
# SimpleJWT normally works with Django's SQL User model.
# We override token generation here to work with our
# mongoengine User document instead.
# ─────────────────────────────────────────────
def get_tokens_for_user(user) -> dict:
    """
    Generate a JWT access + refresh token pair for a mongoengine User document.
    Returns a dict with both token strings.
    """
    # SimpleJWT expects an object with an 'id' attribute — our mongoengine
    # User document has this via its ObjectId primary key
    token = RefreshToken()

    # Embed user identity claims directly into the token payload
    # These are readable on the frontend via token decode if needed
    token['user_id'] = str(user.id)
    token['email']   = user.email
    token['role']    = user.role

    return {
        'refresh': str(token),
        'access':  str(token.access_token),
    }


# ─────────────────────────────────────────────
# SET JWT COOKIES ON A DJANGO RESPONSE OBJECT
#
# This is called after a successful login.
# Both cookies are httpOnly — JavaScript cannot
# read them, which protects against XSS attacks.
# ─────────────────────────────────────────────
def set_auth_cookies(response, access_token: str, refresh_token: str) -> None:
    """
    Attach access and refresh JWT tokens as httpOnly cookies
    to the given Django response object.
    """
    is_secure = getattr(settings, 'JWT_AUTH_COOKIE_SECURE', False)
    samesite  = getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax')

    # Access token cookie — short lived (15 minutes)
    response.set_cookie(
        key      = settings.JWT_AUTH_COOKIE,        # 'access_token'
        value    = access_token,
        max_age  = 60 * 15,                         # 15 minutes in seconds
        httponly = True,
        secure   = is_secure,
        samesite = samesite,
    )

    # Refresh token cookie — long lived (7 days)
    response.set_cookie(
        key      = settings.JWT_AUTH_REFRESH_COOKIE,  # 'refresh_token'
        value    = refresh_token,
        max_age  = 60 * 60 * 24 * 7,                  # 7 days in seconds
        httponly = True,
        secure   = is_secure,
        samesite = samesite,
    )


# ─────────────────────────────────────────────
# CLEAR JWT COOKIES ON LOGOUT
#
# Setting max_age=0 tells the browser to delete
# the cookie immediately.
# ─────────────────────────────────────────────
def clear_auth_cookies(response) -> None:
    """
    Remove both JWT cookies from the browser.
    Called on logout.
    """
    response.delete_cookie(
        key      = settings.JWT_AUTH_COOKIE,
        samesite = getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
    )
    response.delete_cookie(
        key      = settings.JWT_AUTH_REFRESH_COOKIE,
        samesite = getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
    )