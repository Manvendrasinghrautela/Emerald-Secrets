from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')


# ========== SECURITY SETTINGS ==========


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-%0++fr&g^uuw*$9n%sk&9ty78^904ig@y2to7%$@udf&5c*-%=')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'


# Get ALLOWED_HOSTS from environment, with fallback
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# CSRF Trusted Origins for Render deployment
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost,http://127.0.0.1'
).split(',')


# ========== APPLICATION DEFINITION ==========


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # WhiteNoise for static files
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'ecommerce',
    'useraccounts',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'emerald_secrets.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ecommerce.context_processors.cart_count',
            ],
        },
    },
]


WSGI_APPLICATION = 'emerald_secrets.wsgi.application'


# ========== DATABASE CONFIGURATION ==========


# Use DATABASE_URL from environment (provided by Render)
# Falls back to local MySQL for development
if 'DATABASE_URL' in os.environ:
    # Production database (Render PostgreSQL)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local development database (MySQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'emerald_secrets_db',
            'USER': 'root',  # or your MySQL username
            'PASSWORD': 'Kulsm19cphantom@',  # your MySQL password
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
            'CONN_MAX_AGE': 600,
        }
    }


# ========== PASSWORD VALIDATION ==========


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


# ========== INTERNATIONALIZATION ==========


LANGUAGE_CODE = 'en-us'


TIME_ZONE = 'UTC'


USE_I18N = True


USE_TZ = True


# ========== STATIC FILES (CSS, JavaScript, Images) ==========


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if os.path.exists(BASE_DIR / 'static') else []


# WhiteNoise storage configuration for compression and caching
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ========== DEFAULT PRIMARY KEY FIELD TYPE ==========


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ========== CRISPY FORMS ==========


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ========== LOGIN URLS ==========


LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# ========== EMAIL SETTINGS - GMAIL CONFIGURATION ==========

# For development: Use Gmail SMTP
# For production: Use environment variables

if DEBUG:
    # Development: Gmail SMTP with console fallback
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'emeraldsecrets24@gmail.com'
    EMAIL_HOST_PASSWORD = 'tkgt xhfb dqyc xjbk'
    DEFAULT_FROM_EMAIL = 'emeraldsecrets24@gmail.com'
    
    # Timeout for email sending
    EMAIL_TIMEOUT = 10
else:
    # Production: Use environment variables
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'emeraldsecrets24@gmail.com')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '@24emeraldsecrets')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'emeraldsecrets24@gmail.com')
    EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))


# Company email for receiving notifications
COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'emeraldsecrets24@gmail.com')


# ========== REST FRAMEWORK ==========


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# ========== SITE URL ==========


SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')


# ========== PRODUCTION SECURITY SETTINGS ==========


if not DEBUG:
    # Enable HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
    }
