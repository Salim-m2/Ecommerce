# apps/authentication/documents.py

import hashlib
import secrets
from datetime import datetime, timedelta

from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    ObjectIdField,
)


# ─────────────────────────────────────────────
# TOKEN DOCUMENT
#
# Stores secure tokens for two purposes:
# 1. email_verify — sent when a user registers,
#    clicked to activate their account
# 2. password_reset — sent when a user requests
#    a password reset link
#
# We never store the raw token — only a SHA-256
# hash. This means even if the database is
# compromised, the tokens are useless.
#
# A MongoDB TTL index on expires_at automatically
# deletes expired tokens — no cleanup job needed.
# ─────────────────────────────────────────────
class Token(Document):
    user_id    = ObjectIdField(required=True)
    token_hash = StringField(required=True)      # SHA-256 hash of the plain token
    type       = StringField(
                     required=True,
                     choices=['email_verify', 'password_reset']
                 )
    expires_at = DateTimeField(required=True)    # TTL index on this field
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'tokens',
        'indexes': [
            # TTL index — MongoDB auto-deletes documents
            # when expires_at is in the past
            {
                'fields': ['expires_at'],
                'expireAfterSeconds': 0,
            },
            # Fast lookup by user + type
            {'fields': ['user_id', 'type']},
        ],
    }

    # ─────────────────────────────────────────
    # HASH HELPER
    # Converts a plain token string into its
    # SHA-256 hash for safe storage
    # ─────────────────────────────────────────
    @staticmethod
    def hash_token(plain_token: str) -> str:
        """Return the SHA-256 hex digest of a plain token string."""
        return hashlib.sha256(plain_token.encode()).hexdigest()

    # ─────────────────────────────────────────
    # FACTORY METHOD
    # Creates and saves a new Token document,
    # returns the plain token to be sent in email
    # ─────────────────────────────────────────
    @classmethod
    def create_for_user(cls, user, token_type: str, hours_valid: int = 1) -> str:
        """
        Generate a secure random token for a user.

        Saves the hashed version to MongoDB.
        Returns the plain token — caller must send this in the email.

        Args:
            user: mongoengine User document
            token_type: 'email_verify' or 'password_reset'
            hours_valid: how many hours before the token expires

        Returns:
            plain_token (str): the raw token to include in the email link
        """
        # Delete any existing tokens of this type for this user
        # so only one valid reset/verify link exists at a time
        cls.objects(user_id=user.id, type=token_type).delete()

        # Generate a cryptographically secure random token
        plain_token = secrets.token_urlsafe(32)

        # Store only the hash — never the plain token
        token_doc = cls(
            user_id    = user.id,
            token_hash = cls.hash_token(plain_token),
            type       = token_type,
            expires_at = datetime.utcnow() + timedelta(hours=hours_valid),
        )
        token_doc.save()

        return plain_token

    @classmethod
    def verify_token(cls, plain_token: str, token_type: str):
        """
        Look up a token by its hash and type.
        Returns the Token document if valid, None if not found or expired.

        MongoDB's TTL index handles deletion of expired tokens,
        but we also check expiry manually as a safety net.
        """
        token_hash = cls.hash_token(plain_token)

        try:
            token_doc = cls.objects.get(
                token_hash = token_hash,
                type       = token_type,
            )
        except cls.DoesNotExist:
            return None

        # Manual expiry check as a safety net
        if token_doc.expires_at < datetime.utcnow():
            token_doc.delete()
            return None

        return token_doc

    def __str__(self):
        return f"Token({self.type}, user={self.user_id}, expires={self.expires_at})"