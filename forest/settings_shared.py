# Django settings for forest project.
import os.path
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ( )

MANAGERS = ADMINS

DATABASES = {
    'default' : {
        'ENGINE' : 'django.db.backends.postgresql_psycopg2',
        'NAME' : 'forest',
        'HOST' : '',
        'PORT' : 5432,
        'USER' : '',
        'PASSWORD' : '',
        }
}

if 'test' in sys.argv:
    DATABASE_ENGINE = 'sqlite3'
SOUTH_TESTS_MIGRATE = False
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

USE_TZ = True
TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
MEDIA_ROOT = "/var/www/forest/uploads/"
MEDIA_URL = '/uploads/'
STATIC_URL = '/media/'
SECRET_KEY = ')ng#)ef_u@_^zvvu@dxm7ql-yb^_!a6%v3v^j3b(mp+)l+5%@h'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    )

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'forest.urls'

TEMPLATE_DIRS = (
    "/var/www/forest/templates/",
    os.path.join(os.path.dirname(__file__),"/templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'staticmedia',
    'sorl.thumbnail',
    'django.contrib.admin',
    'tagging',
    'smartif',
    'template_utils',
    'typogrify',
    'raven.contrib.django',
    'munin',
    'pagetree',
    'pageblocks',
    'forest.main',
    'quizblock',
    'careermapblock',
    'fridgeblock',
    'south',
    'django_nose',
    'compressor',
    'django_statsd',
)

PAGEBLOCKS = ['pageblocks.TextBlock',
              'pageblocks.HTMLBlock',
              'pageblocks.PullQuoteBlock',
              'pageblocks.ImageBlock',
              'pageblocks.ImagePullQuoteBlock',
              'quizblock.Quiz',
              'careermapblock.CareerMap',
              'fridgeblock.FridgeBlock',
              ]


SENTRY_REMOTE_URL = 'http://sentry.ccnmtl.columbia.edu/sentry/store/'
# remember to set the SENTRY_KEY in a local_settings.py
# as documented in the wiki
SENTRY_SITE = 'forest'

THUMBNAIL_SUBDIR = "thumbs"
EMAIL_SUBJECT_PREFIX = "[forest] "
EMAIL_HOST = 'localhost'
SERVER_EMAIL = "forest@ccnmtl.columbia.edu"

# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', 'sitemedia'),
)

COMPRESS_URL = "/site_media/"
COMPRESS_ROOT = "media/"
COMPRESS_PARSER = "compressor.parser.HtmlParser"

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.WindAuthBackend','django.contrib.auth.backends.ModelBackend',)
WIND_BASE = "https://wind.columbia.edu/"
WIND_SERVICE = "cnmtl_full_np"
WIND_PROFILE_HANDLERS = ['djangowind.auth.CDAPProfileHandler']
WIND_AFFIL_HANDLERS = ['djangowind.auth.AffilGroupMapper','djangowind.auth.StaffMapper','djangowind.auth.SuperuserMapper']
WIND_STAFF_MAPPER_GROUPS = ['tlc.cunix.local:columbia.edu']
WIND_SUPERUSER_MAPPER_GROUPS = ['anp8','jb2410','zm4','sbd12','egr2107','kmh2124','sld2131','amm8','mar227','ed2198', 'ej2223']

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'forest'
STATSD_HOST = 'localhost'
STATSD_PORT = 8125
STATSD_PATCHES = ['django_statsd.patches.db', ]
