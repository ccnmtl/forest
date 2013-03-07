# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/forest/forest/forest/templates",
)

MEDIA_ROOT = '/var/www/forest/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/forest/forest/sitemedia'),
)

COMPRESS_ROOT = "/var/www/forest/forest/media/"

DEBUG = False
TEMPLATE_DEBUG = DEBUG
STAGING_ENV = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'forest',
        'HOST': '',
        'PORT': 6432,
        'USER': '',
        'PASSWORD': '',
    }
}

STATSD_PREFIX = 'forest-staging'
SENTRY_SITE = 'forest-staging'
SENTRY_SERVERS = ['http://sentry.ccnmtl.columbia.edu/sentry/store/']

if 'migrate' not in sys.argv:
    import logging
    from raven.contrib.django.handlers import SentryHandler
    logger = logging.getLogger()
    # ensure we havent already registered the handler
    if SentryHandler not in map(type, logger.handlers):
        logger.addHandler(SentryHandler())

        logger = logging.getLogger('sentry.errors')
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())


try:
    from local_settings import *
except ImportError:
    pass
