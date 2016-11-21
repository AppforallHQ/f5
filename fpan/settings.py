# Django settings for fpan project.
import os
import analytics,logging
from .env import *

if not os.environ.get('DEVELOPMENT', False):
    from .prod_env import *

DEBUG = (os.environ.get('DEVELOPMENT', False)=="1")
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Tehran'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '!b@1+y9(6@1es#m3t=_)sq(x)q)gf+_#t$grt#7zqh%b+t_-m4'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'apiv2.middleware.TokenSessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'tokenapi.backends.TokenBackend'
)

ROOT_URLCONF = 'fpan.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'fpan.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django_coverage',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    #'kombu.transport.django',
    'payment',
    'plans',
    'cron',
    'apiv1',
    'apiv2',
    'generic',
    'lettuce.django',
#    'south',
    'rest_framework',
#    'djcelery',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('apiv1.authentication.SuperUserSessionAuthentication',
                                       'apiv1.authentication.TokenAPIAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'PAGINATE_BY': 10
}

LOGGING = {
   'version': 1,
   'disable_existing_loggers': False,
   'formatters': {
      'django': {
         'format':'django F5: %(message)s',
       },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
   'handlers': {
      'logging.handlers.SysLogHandler': {
         'level': 'DEBUG',
         'class': 'logging.handlers.SysLogHandler',
         'facility': 'local7',
         'formatter': 'django',
         'address' : '/dev/log',
       },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler'
        }
   },

   'loggers': {
       'django': {
           'handlers': ['logging.handlers.SysLogHandler', 'console'],
           'level': 'WARNING',
           'propagate': True,
       },
      'loggly_logs':{
         'handlers': ['logging.handlers.SysLogHandler'],
         'propagate': True,
         'format':'django: %(message)s',
         'level': 'DEBUG',
       },
       'analytics': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}


# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES = {
    'default':  dj_database_url.parse(DATABASE_URL),
}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_NAME = 'SOME_SESSION_ID'

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')
STATIC_URL = '/fpan/static/'
ADMIN_MEDIA_PREFIX = '/fpan/static/admin/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'


#THIS IS NOT SECURE DUE TO DJANGO 1.6 DOCS
#PLEASE TRY TO USE JSON Serializer
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


OMGPAY_MOCK_BANK_GATEWAY = False
OMGPAY_ACTIVE_GATEWAYS = ["mellat"]
DAYS_BEFORE_SUBSCRIPTION_START = 14

AUTH_USER_MODEL = 'auth.User'

if not os.environ.get('DEVELOPMENT', False):
    from .settings_production import *
    
    INSTALLED_APPS += (
        'raven.contrib.django.raven_compat',
    )
# as mentioned in [https://segment.io/docs/libraries/python/], we should
# initiate the analytics package in urls.py, but celery would not
# load the setup for us, so we initiate analytics package here
analytics.write_key = ANALYTICS_API  

# Payment data
MELLAT_PAYMENT = {
    "TERMINAL_ID": "",
    "USERNAME": "",
    "PASSWORD": ""
}

PASARGAD_PAYMENT = {
    "MERCHANT_CODE": "",
    "TERMINAL_CODE": "",
}
