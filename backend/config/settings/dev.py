# config/settings/dev.py

from .base import *

# ─────────────────────────────────────────────
# DEVELOPMENT OVERRIDES
# ─────────────────────────────────────────────

DEBUG = True

# Allow Django's dev server
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# JWT cookies do not require HTTPS in development
JWT_AUTH_COOKIE_SECURE = False

# Show emails in the terminal instead of sending them
# (we wire up SendGrid properly in Week 8)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable throttling in development so it doesn't
# block you while testing endpoints repeatedly
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}