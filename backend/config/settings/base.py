# config/settings/base.py

import os
from pathlib import Path
from datetime import timedelta
import environ
import mongoengine
import cloudinary

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────
# ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, True),
    
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ─────────────────────────────────────────────
# CORE SETTINGS
# ─────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ─────────────────────────────────────────────
# INSTALLED APPS
# ─────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.auth',          # required by simplejwt
    'django.contrib.sessions',      # required by auth
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.users',
    'apps.core',
    'apps.products',
    'apps.cart',  
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ─────────────────────────────────────────────
# URLS & WSGI
# ─────────────────────────────────────────────
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ─────────────────────────────────────────────
# TEMPLATES (minimal — needed for email templates later)
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ─────────────────────────────────────────────
# DATABASE
# We are using mongoengine exclusively — no Django ORM / SQL
# ─────────────────────────────────────────────
# Provide a minimal dummy DB config so Django internals
# (contenttypes, etc.) don't crash — mongoengine handles all real data
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─────────────────────────────────────────────
# AUTHENTICATION BACKENDS
# Replace Django's default SQL auth with our
# custom MongoDB backend
# ─────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.MongoAuthBackend',
]

# ─────────────────────────────────────────────
# MONGODB CONNECTION (mongoengine)
# ─────────────────────────────────────────────
mongoengine.connect(
    db=env('MONGO_DB'),
    host=env('MONGO_URI'),
    alias='default',
)

# Cloudinary
cloudinary.config(
    cloud_name=env('CLOUDINARY_CLOUD_NAME'),
    api_key=env('CLOUDINARY_API_KEY'),
    api_secret=env('CLOUDINARY_API_SECRET'),
    secure=True,          # Always use HTTPS URLs
)

# Ensure MongoDB indexes exist on every startup.
# create_index() is idempotent — safe to call repeatedly.
from apps.products.indexes import create_product_indexes

create_product_indexes()

# ─────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.authentication.authentication.MongoJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '10/minute',       # applied explicitly on the login view
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─────────────────────────────────────────────
# SIMPLE JWT
# ─────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# JWT Cookie settings (custom — used in our auth views)
JWT_AUTH_COOKIE = 'access_token'
JWT_AUTH_REFRESH_COOKIE = 'refresh_token'
JWT_AUTH_COOKIE_HTTP_ONLY = True
JWT_AUTH_COOKIE_SAMESITE = 'Lax'
JWT_AUTH_COOKIE_SECURE = False      # overridden to True in prod.py

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
CORS_ALLOW_CREDENTIALS = True       # required for cookies to be sent cross-origin
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173'],
)

# ─────────────────────────────────────────────
# INTERNATIONALIZATION
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ─────────────────────────────────────────────
# MEDIA FILES (local dev only — production uses Cloudinary)
# ─────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────
# CELERY (broker wired up in Week 8 — placeholder kept here)
# ─────────────────────────────────────────────
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ─────────────────────────────────────────────
# LOGGING (basic — keeps sensitive data out of logs)
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}