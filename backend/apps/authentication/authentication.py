# apps/authentication/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions
from apps.users.documents import User


# ─────────────────────────────────────────────
# CUSTOM JWT AUTHENTICATION
#
# Django's default JWTAuthentication tries to look
# up the user in a SQL database. We override it to
# look up our mongoengine User document instead.
# ─────────────────────────────────────────────
class MongoJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        """
        Read the JWT from the httpOnly cookie first.
        Fall back to the Authorization header for API clients.
        """
        # Try reading from httpOnly cookie first
        from django.conf import settings
        cookie_name = getattr(settings, 'JWT_AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)

        # Fall back to Authorization header if no cookie
        if raw_token is None:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

        # Validate the token
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # Get the user from MongoDB using the token payload
        user = self.get_user(validated_token)

        return user, validated_token

    def get_user(self, validated_token):
        """
        Look up the mongoengine User document using
        the user_id claim embedded in the JWT payload.
        """
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found.', code='user_not_found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User is inactive.', code='user_inactive')

        # Attach user_id to the request for easy access in views
        return user