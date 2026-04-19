# apps/authentication/serializers.py

from rest_framework import serializers
from apps.users.documents import User


# ─────────────────────────────────────────────
# REGISTER SERIALIZER
#
# Validates all fields required to create a new
# user account. Runs before any database writes.
# ─────────────────────────────────────────────
class RegisterSerializer(serializers.Serializer):
    first_name       = serializers.CharField(
                           max_length=100,
                           error_messages={'blank': 'First name is required.'}
                       )
    last_name        = serializers.CharField(
                           max_length=100,
                           error_messages={'blank': 'Last name is required.'}
                       )
    email            = serializers.EmailField(
                           error_messages={'blank': 'Email is required.'}
                       )
    password         = serializers.CharField(
                           min_length=8,
                           write_only=True,    # never returned in responses
                           error_messages={
                               'min_length': 'Password must be at least 8 characters.',
                               'blank': 'Password is required.',
                           }
                       )
    confirm_password = serializers.CharField(
                           write_only=True,
                           error_messages={'blank': 'Please confirm your password.'}
                       )

    def validate_email(self, value: str) -> str:
        """Ensure the email is not already registered."""
        email = value.lower().strip()
        if User.objects(email=email).first():
            raise serializers.ValidationError(
                'An account with this email already exists.'
            )
        return email

    def validate(self, data: dict) -> dict:
        """Ensure both password fields match."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data


# ─────────────────────────────────────────────
# LOGIN SERIALIZER
#
# Validates that email and password fields are
# present and non-empty. Actual credential
# verification happens in the view via the
# auth backend.
# ─────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField(
                   error_messages={'blank': 'Email is required.'}
               )
    password = serializers.CharField(
                   write_only=True,
                   error_messages={'blank': 'Password is required.'}
               )

    def validate_email(self, value: str) -> str:
        """Normalize email to lowercase before lookup."""
        return value.lower().strip()


# ─────────────────────────────────────────────
# USER SERIALIZER
#
# Safe read-only representation of a user.
# Returned in login responses and /auth/me/.
# Never exposes password_hash.
# ─────────────────────────────────────────────
class UserSerializer(serializers.Serializer):
    id         = serializers.SerializerMethodField()
    email      = serializers.EmailField()
    role       = serializers.CharField()
    first_name = serializers.CharField()
    last_name  = serializers.CharField()
    full_name  = serializers.SerializerMethodField()
    avatar_url = serializers.CharField()
    is_verified = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    def get_id(self, obj) -> str:
        """Return MongoDB ObjectId as a plain string."""
        return str(obj.id)

    def get_full_name(self, obj) -> str:
        return obj.full_name


# ─────────────────────────────────────────────
# CHANGE PASSWORD SERIALIZER
#
# Used in the user profile section (Week 10).
# Defined here so it lives with auth-related
# serializers.
# ─────────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
                           write_only=True,
                           error_messages={'blank': 'Current password is required.'}
                       )
    new_password     = serializers.CharField(
                           min_length=8,
                           write_only=True,
                           error_messages={
                               'min_length': 'New password must be at least 8 characters.',
                               'blank': 'New password is required.',
                           }
                       )
    confirm_password = serializers.CharField(
                           write_only=True,
                           error_messages={'blank': 'Please confirm your new password.'}
                       )

    def validate(self, data: dict) -> dict:
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data