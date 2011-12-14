from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/forest/forest/templates",
)

MEDIA_ROOT = '/var/www/forest/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/forest/forest/sitemedia'),	
)

COMPRESS_ROOT = "/var/www/forest/forest/media/"

import logging
from sentry.client.handlers import SentryHandler
logger = logging.getLogger()
if SentryHandler not in map(lambda x: x.__class__, logger.handlers):
    logger.addHandler(SentryHandler())
    logger = logging.getLogger('sentry.errors')
    logger.propagate = False
    logger.addHandler(logging.StreamHandler())


DEBUG = False
TEMPLATE_DEBUG = DEBUG

try:
    from local_settings import *
except ImportError:
    pass
