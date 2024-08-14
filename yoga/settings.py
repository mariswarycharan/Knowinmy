"""
Django settings for yoga project.

Generated by 'django-admin startproject' using Django 3.2.15.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SETTINGS_PATH = os.path.dirname(os.path.dirname(__file__))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2@d_u@j&$$o$l^0z_6p+y#^ewn1a)m#wy0#(0nkw@doy9x0v3p'

# SECURITY WARNING: don't run with debug turned on in production!

IS_PRODUCTION = os.environ.get('IS_PRODUCTION', False)
DEBUG = not IS_PRODUCTION

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'celery',
    'django_celery_results',


    'users',
    'crispy_forms',
    'import_export',
    'tablib',
    'openpyxl',
    'sweetify',
 
    # 'django_celery_beat',
    # 'django_celery_results',

    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'users.middleware.idempotent_post_middleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'yoga.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                
            ],
        },
    },
]

WSGI_APPLICATION = 'yoga.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
if IS_PRODUCTION:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_USER'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': 'postgres',
            'PORT': os.environ.get('POSTGRES_PORT'),
            'ATOMIC_REQUESTS': True,
        }
    }
else: 
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'ATOMIC_REQUESTS': True,
        }   
    }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '/')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#media
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


#crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'


LOGIN_URL='/login/'
LOGIN_REDIRECT_URL= '/'

CSRF_TRUSTED_ORIGINS = ["https://test1.knowinmy.com", "https://staging.knowinmy.com","http://10.1.76.75" "http://10.1.76.152"]
#if IS_PRODUCTION:
#    SECURE_SSL_REDIRECT = True







#SMTP CONFIGURATION 

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.example.com'  # SMTP server host
EMAIL_PORT = 587  # SMTP server port (587 for TLS, 465 for SSL)
EMAIL_HOST_PORT = 25    
EMAIL_USE_TLS = True  # True for TLS, False for SSL




# RAZORPAY INTEGERATION 
RAZORPAY_KEY_ID='rzp_test_gH8crtxqRW3cZr' 
RAZORPAY_KEY_SECRET='EMEAVJGJAygp5zbJh5MSjkXY'

#social app custom settings
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    # 'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

LOGIN_URL = 'login/'
LOGIN_REDIRECT_URL = 'http://localhost:8000/social-auth/complete/google-oauth2/'
LOGOUT_URL = 'logout'
LOGOUT_REDIRECT_URL = 'login/'




SOCIAL_AUTH_GOOGLE_OAUTH2_KEY='60405106027-3313c38rudkdq40kbecod7ph6h01kiih.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET ='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'




# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Don't expire the session when the browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Save the session to extend its expiry on every request










sentry_sdk.init(
    dsn="https://28471d1821c73d7bd3d41744c4f43765@o4507736382636032.ingest.us.sentry.io/4507736387616768",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,integrations=[DjangoIntegration()],
   
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)










CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6380/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}




CELERY_BROKER_URL = "redis://localhost:6380"
CELERY_RESULT_BACKEND='django-db'
