# apps/authentication/backends.py

from apps.users.documents import User


# ─────────────────────────────────────────────
# CUSTOM MONGODB AUTHENTICATION BACKEND
#
# Django's default backend checks its SQL User table.
# We replace that with a mongoengine lookup against
# our User document in MongoDB Atlas.
#
# Django calls authenticate(request, email=..., password=...)
# and expects either a user object or None back.
# ─────────────────────────────────────────────
class MongoAuthBackend:

    def authenticate(self, request, email: str = None, password: str = None):
        """
        Look up a user by email, verify their password.
        Returns the User document on success, None on failure.
        """
        if not email or not password:
            return None

        try:
            # Lookup is case-insensitive — .lower() prevents
            # 'Jane@example.com' and 'jane@example.com' being treated as different users
            user = User.objects.get(email=email.lower().strip())
        except User.DoesNotExist:
            # Run a dummy check anyway to prevent timing attacks —
            # an attacker shouldn't be able to tell if the email exists
            # based on how fast the server responds
            User(password_hash='!').check_password(password)
            return None

        # Verify the password against the stored bcrypt hash
        if not user.check_password(password):
            return None

        # Deactivated accounts cannot log in
        if not user.is_active:
            return None

        return user

    def get_user(self, user_id: str):
        """
        Django calls this to reload the user from the session.
        We look up by MongoDB ObjectId string.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None