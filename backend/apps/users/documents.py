# apps/users/documents.py

from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    BooleanField,
    DateTimeField,
    ListField,
    EmbeddedDocumentField,
)


# ─────────────────────────────────────────────
# EMBEDDED DOCUMENT — Address
# Stored inside the User document as a list
# ─────────────────────────────────────────────
class Address(EmbeddedDocument):
    label      = StringField(max_length=50, default='Home')   # e.g. "Home", "Work"
    street     = StringField(max_length=255, required=True)
    city       = StringField(max_length=100, required=True)
    country    = StringField(max_length=100, default='Kenya')
    is_default = BooleanField(default=False)

    def __str__(self):
        return f"{self.label} — {self.street}, {self.city}"


# ─────────────────────────────────────────────
# MAIN DOCUMENT — User
# This replaces Django's built-in User model entirely.
# All authentication, roles, and profile data live here.
# ─────────────────────────────────────────────
class User(Document):
    email         = StringField(max_length=255, required=True, unique=True)
    password_hash = StringField(required=True)
    role          = StringField(
                        max_length=20,
                        choices=['customer', 'seller', 'admin'],
                        default='customer'
                    )
    first_name    = StringField(max_length=100, required=True)
    last_name     = StringField(max_length=100, required=True)
    phone         = StringField(max_length=20, default='')
    avatar_url    = StringField(max_length=500, default='')

    # Email verification — set to True after user clicks the link in Week 8
    is_verified   = BooleanField(default=False)

    # Soft disable — deactivated users cannot log in
    is_active     = BooleanField(default=True)

    # Embedded list of addresses — stored directly in this document
    addresses     = ListField(EmbeddedDocumentField(Address), default=list)

    created_at    = DateTimeField(default=datetime.utcnow)
    last_login    = DateTimeField(null=True)

    meta = {
        'collection': 'users',      # MongoDB collection name
        'indexes': [
            {'fields': ['email'], 'unique': True},  # fast lookup by email
        ],
        'ordering': ['-created_at'],
    }

    # ─────────────────────────────────────────
    # PASSWORD METHODS
    # Never store raw passwords — always hash
    # ─────────────────────────────────────────
    def set_password(self, raw_password: str) -> None:
        """Hash raw_password and store it. Call this on register and password reset."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Return True if raw_password matches the stored hash."""
        return check_password(raw_password, self.password_hash)

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_default_address(self):
        """Return the address marked as default, or None."""
        for address in self.addresses:
            if address.is_default:
                return address
        return None

    def __str__(self):
        return f"{self.full_name} <{self.email}>"