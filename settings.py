import os

import dj_database_url
from django.urls import reverse_lazy

APP_NAME = 'kidviz'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INTERNAL_IPS = ['127.0.0.1']

# BASIC DJANGO SETTINGS

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'RESETME')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('USE_SSL', 'False') == 'True'
ALLOWED_HOSTS = '*'

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
USE_L10N = True
USE_TZ = True
ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

# MAIL SETTINGS
EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
ANYMAIL = {
    'MAILGUN_API_KEY': os.getenv('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_DOMAIN'),
    'AMAZON_SES_CLIENT_PARAMS': {
        'region_name': 'us-east-1'
    }
}
DEFAULT_FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@kidviz.local')

# APP AND MIDDLEWARE SETTINGS

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]
BACKEND_THIRD_PARTY_APPS = [
    'django_extensions',  # all kinds of goodness
    'raven.contrib.django.raven_compat',  # sentry-django connector
    'allauth',  # Authentication/Registration
    'allauth.account',  # Authentication/Registration
    'formtools',  # for wizard views
    'storages',  # for S3-backed media
    's3file', # for S3 direct upload
    'anymail',  # for mailgun emails
]

FRONTEND_THIRD_PARTY_APPS = [
    'bootstrap4',  # handy b4 template tags
    'tz_detect',  # async JS timezone detector
    'related_select',  # for AJAX-powered related select boxes
    'tinymce',  # for HTML editor for sublevel examples
    'active_link',  # for easy active classes
    'import_export',  # for file uploads
]
LOCAL_APPS = [
    'users',
    'kidviz',
]
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + BACKEND_THIRD_PARTY_APPS + FRONTEND_THIRD_PARTY_APPS

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'kidviz.middleware.S3FileMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
    'middleware.DjangoThreadLocalMiddleware',
]

if DEBUG:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

# DATABASES AND CACHING

DATABASES = {}
# local database uses old name for now
DATABASES['default'] = dj_database_url.config(
    conn_max_age=600,
    default=os.environ.get('DATABASE_URL', 'postgres://localhost:5432/lsoa')
)

# TEMPLATES AND STATIC FILES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'kidviz.context_processors.has_current_observation',
            ],
        },
    },
]
if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# AUTHENTICATION SETTINGS

ACCOUNT_AUTHENTICATION_METHOD = 'email'  # require email instead of username
ACCOUNT_EMAIL_REQUIRED = True  # require email instead of username
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # so that users must confirm their e-mail address first
ACCOUNT_LOGOUT_REDIRECT_URL = reverse_lazy('account_login')
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # we no longer have a username field (email instead)
ACCOUNT_USERNAME_REQUIRED = False  # require email instead of username
ACCOUNT_ADAPTER = 'users.adapters.PendingUserAccountAdapter'  # allows correct "pending approval" flow
AUTH_USER_MODEL = 'users.User'  # to use our model instead of the default Django one (ours uses email == username)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
LOGIN_URL = reverse_lazy('account_login')  # to use allauth instead of django admin login page
LOGIN_REDIRECT_URL = '/'  # TODO

# SENTRY AND LOGGING SETTINGS
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_DSN', ''),
    # MUST USE "heroku labs:enable runtime-dyno-metadata -a <app name>"
    'release': os.getenv('HEROKU_SLUG_COMMIT', 'DEBUG'),
    'environment': os.getenv('HEROKU_ENVIRONMENT', 'local'),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # disabling this messes up default django logging
    'root': {
        'level': 'DEBUG' if DEBUG else 'INFO',
        'handlers': ['console', 'sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# MEDIA SETTINGS
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = 'us-east-2'

# OTHER PLUGIN SETTINGS
TINYMCE_DEFAULT_CONFIG = {'height': 400, 'width': 600}
