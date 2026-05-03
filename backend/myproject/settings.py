from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG_INTENT_LOG_FILE = BASE_DIR / 'checkjson.log'
SECRET_KEY = 'django-insecure-#-q_^(f#_-$e73z^0$-@r3duc9!y_^b*re3*&6cinnfzz&p6c!'
# STRIPE_PREMIUM_PRICE_ID = "price_1SqV5EFDCAdx0wmRYACLZs98"

DEBUG = False
load_dotenv() 
REDIS_URL = (
    os.getenv("REDIS_PRIVATE_URL")   # Railway internal (backend dùng cái này)
    or os.getenv("REDIS_URL")        # fallback
    or os.getenv("REDIS_PUBLIC_URL") # fallback cuối
)

if not REDIS_URL:
    raise Exception("Redis is required but no Redis URL found in environment variables.")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
ALLOWED_HOSTS = [
    "api.vietcloud.work",
    "vietcloud.work",
    "www.vietcloud.work",

    ".railway.app",

    "localhost",
    "127.0.0.1",

    "finalproject-seven-teal.vercel.app",
]
# =========================
# RESEND EMAIL CONFIG
# =========================
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
DEFAULT_FROM_EMAIL = "VietCloud <no-reply@vietcloud.work>"
# ----------------------
# Installed Apps
# ----------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'api',
]

# ----------------------
# Middleware
# ----------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 🡐 corsheaders lên trên CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ----------------------
# Database
# ----------------------
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'vietcloud_db',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': 'mongodb+srv://phamdiep400dn_db_user:omGkBX6v1uqeHlfY@vietcloud.5gnveh4.mongodb.net/?appName=vietcloud'
        }
    }
}

# ----------------------
# Cache
# ----------------------
# Sử dụng django-redis (đã cài django-redis==4.12.1 và redis==3.5.3)
# Cache chỉ lưu dữ liệu API (weather, geocoding) — KHÔNG dùng cho session hoặc JWT
CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,  # không crash nếu Redis lỗi
            },
            "KEY_PREFIX": "vietcloud",
        }
    }


# ----------------------
# Password Validators
# ----------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# ----------------------
# Language / Timezone
# ----------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------
# CORS / CSRF / Cookies
# ----------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "https://finalproject-production-b074.up.railway.app",
    "https://finalproject-seven-teal.vercel.app",
    "https://vietcloud.work",
    "https://www.vietcloud.work",
    "https://api.vietcloud.work",
]
CORS_ALLOW_CREDENTIALS = True   

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "https://finalproject-production-b074.up.railway.app",
    "https://finalproject-seven-teal.vercel.app",
    "https://vietcloud.work",
    "https://www.vietcloud.work",
    "https://api.vietcloud.work",
]

# Cookie settings - tự động theo môi trường
import os
_is_production = os.getenv('RAILWAY_ENVIRONMENT') == 'production'

SESSION_COOKIE_SECURE = _is_production   # True when deploy HTTPS
CSRF_COOKIE_SECURE = _is_production
SESSION_COOKIE_SAMESITE = 'None' if _is_production else 'Lax'
CSRF_COOKIE_SAMESITE = 'None' if _is_production else 'Lax'
# ===============================
# CROSS SUBDOMAIN COOKIE (CRITICAL)
# ===============================

SESSION_COOKIE_DOMAIN = ".vietcloud.work"
CSRF_COOKIE_DOMAIN = ".vietcloud.work"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"


# ----------------------
# REST Framework / JWT
# ----------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.CustomJWTAuthentication',  # đọc token từ cookie
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ----------------------
# Logging Configuration
# ----------------------
import sys

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # để Django không tắt các logger mặc định
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',  # file log ghi ra cùng thư mục project
            'formatter': 'verbose',
        },
        'intent_file': {
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'checkjson.log',
        'formatter': 'verbose',
        'mode': 'a',   # append (ta sẽ clear bằng code)
        },
        'cron_file': {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "cron.log"),
            'formatter': 'verbose',
        },
    },
        'loggers': {
        'api.views.weather_views': {  
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.views.map_views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.views.verifyotp_views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.views.auth_views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },  
        'api.views.chatbot_views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },  
        'api.views.weather_intent_views': {
            'handlers': ['intent_file'],
            'level': 'DEBUG',
            'propagate': False,   # ❗ không đẩy sang debug.log
        },
                     
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'cron.expire_premium': {
            'handlers': ['cron_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },


}