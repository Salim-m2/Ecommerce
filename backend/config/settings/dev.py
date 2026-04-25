# config/settings/dev.py

from .base import *

# ─────────────────────────────────────────────
# DEVELOPMENT OVERRIDES
# ─────────────────────────────────────────────

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# JWT cookies do not require HTTPS in development
JWT_AUTH_COOKIE_SECURE = False

# Show emails in the terminal instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable global throttling in development so repeated
# test requests don't get blocked — but keep the login
# rate defined so LoginRateThrottle doesn't crash
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '10000/hour',
    'login': '100/minute',   # high limit for dev — still needs to exist
}

