"""
Django settings for ai_platform project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,10.10.173.12,192.168.1.11,django').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',  # Our API app
    'django_celery_beat',  # Celery Beat 排程
    'django_celery_results',  # Celery 結果存儲
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'api.middleware.DisableCSRFMiddleware',  # 在 CSRF 中間件之前
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'api.middleware.UserProfileMiddleware',  # 在認證中間件之後
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_platform.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='ai_platform'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres123'),
        'HOST': config('DB_HOST', default='postgres_db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TZ', default='Asia/Taipei')
USE_I18N = True
USE_TZ = False  # 關閉 UTC 時區轉換，直接使用本地時區

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.10.173.12",
    "http://localhost",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # 安全性考量
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.10.173.12",
    "http://localhost",
]

# 排除特定路徑的 CSRF 檢查
CSRF_EXEMPT_URLS = [
    '/api/auth/login/',
    '/api/auth/logout/',
    '/api/dify/',
    '/api/rvt-guide/',
    '/api/protocol-assistant/',  # Protocol Assistant Chat API
]

# Session settings for authentication
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # 開發環境設為 False
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_DOMAIN = None  # 允許所有域名
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SAVE_EVERY_REQUEST = True  # 確保每次請求都保存 session

# 增加 CSRF Cookie 設定
CSRF_COOKIE_HTTPONLY = False  # 允許 JavaScript 讀取 CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # 開發環境設為 False
CSRF_USE_SESSIONS = False  # 使用獨立的 CSRF cookie

# Whitenoise settings
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# File Upload Settings
# 設置文件上傳大小限制 (50MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} | {name} | {funcName} | Line {lineno} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{levelname}] {asctime} | PID:{process:d} | Thread:{thread:d} | {name} | {funcName} | Line {lineno} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # 按日期分割的一般 log（每天午夜輪替，保留 30 天）
        'daily_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/django.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,  # 保留 30 天
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # 按日期分割的錯誤 log（保留 60 天）
        'daily_error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/django_error.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 60,  # 錯誤 log 保留更久
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # Dify 請求專用 log（按日期輪替，保留 20 天）
        'dify_requests_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/dify_requests.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 20,
            'formatter': 'detailed',  # 使用詳細格式
            'encoding': 'utf-8',
        },
        # RVT Analytics 專用 log
        'rvt_analytics_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/rvt_analytics.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 15,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # Vector 操作專用 log
        'vector_operations_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/vector_operations.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 15,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # API 訪問記錄（輕量級）
        'api_access_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/api_access.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,  # API 訪問只保留 7 天
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
        # Celery 任務 log
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/app/logs/celery.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # API Views
        'api.views': {
            'handlers': ['console', 'daily_file', 'daily_error_file', 'api_access_file'],
            'level': 'INFO',
            'propagate': True,
        },
        # Django 核心
        'django': {
            'handlers': ['console', 'daily_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django Request（API 訪問）
        'django.request': {
            'handlers': ['console', 'daily_file', 'api_access_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Library 模組（一般）
        'library': {
            'handlers': ['console', 'daily_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Dify 整合專用
        'library.dify_integration': {
            'handlers': ['console', 'dify_requests_file', 'daily_error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # RVT Analytics
        'library.rvt_analytics': {
            'handlers': ['console', 'rvt_analytics_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Vector 服務
        'api.services.embedding_service': {
            'handlers': ['console', 'vector_operations_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Celery
        'celery': {
            'handlers': ['console', 'celery_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Protocol Guide
        'library.protocol_guide': {
            'handlers': ['console', 'daily_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # RVT Guide
        'library.rvt_guide': {
            'handlers': ['console', 'daily_file', 'daily_error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'daily_file', 'daily_error_file'],
        'level': 'INFO',
    },
}

# ============================
# Celery 配置
# ============================

# Redis 配置
REDIS_HOST = config('REDIS_HOST', default='redis')  # Docker 服務名
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_DB = config('REDIS_DB', default=0, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')

# Celery 配置
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"
CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/2"

# Celery 任務配置
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Taipei'
CELERY_ENABLE_UTC = False

# Celery Beat 配置 (定時任務)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE_FILENAME = 'celerybeat-schedule'

# 任務路由和佇列配置
CELERY_TASK_ROUTES = {
    'library.rvt_analytics.tasks.*': {'queue': 'analytics'},
    'library.rvt_guide.tasks.*': {'queue': 'rvt_guide'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# 任務結果過期時間 (1小時)
CELERY_RESULT_EXPIRES = 3600

# ============================
# Redis Cache 配置
# ============================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'ai_platform',
        'TIMEOUT': 3600,  # 1小時默認過期時間
    }
}