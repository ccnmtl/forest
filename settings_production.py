from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/forest/forest/templates",
)

MEDIA_ROOT = '/var/www/forest/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/forest/forest/sitemedia'),	
)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

try:
    from local_settings import *
except ImportError:
    pass
