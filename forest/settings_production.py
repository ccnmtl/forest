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

STATICFILES_DIRS = ()
STATIC_ROOT = "/var/www/forest/forest/media/"

if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

SEED_STAND = "forest.ccnmtl.columbia.edu"

try:
    from local_settings import *
except ImportError:
    pass
