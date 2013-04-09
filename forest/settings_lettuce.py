# flake8: noqa
from settings_shared import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'lettuce.db',
        'OPTIONS': {
            'timeout': 30,
        }
    }
}

LETTUCE_APPS = (
    'forest.main',
)

LETTUCE_SERVER_PORT = 8002
STATSD_HOST = '127.0.0.1'
BROWSER = 'Chrome'

if os.environ.get('SELENIUM_BROWSER', False):
    # it's handy to be able to set this from an
    # environment variable
    BROWSER = os.environ.get('SELENIUM_BROWSER')
