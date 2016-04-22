# flake8: noqa
# Django settings for forest project.
import os.path
import sys
from ccnmtlsettings.shared import common


project = 'forest'
base = os.path.dirname(__file__)

locals().update(common(
    project=project,
    base=base,
))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake-forest'
    }
}

if 'test' in sys.argv or 'jenkins' in sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        }

PROJECT_APPS = [
    'forest.main',
]

USE_TZ = True

EPUB_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates/epub/")

INSTALLED_APPS += [  # noqa
    'bootstrap3',
    'sorl.thumbnail',
    'pagetree',
    'pageblocks',
    'forest.main',
    'quizblock',
    'careermapblock',
    'fridgeblock',
    'bootstrapform',
    'django_extensions',
    'likertblock',
]

TEMPLATE_CONTEXT_PROCESSORS += [  # noqa
    'forest.main.views.context_processor',
]

PAGEBLOCKS = ['pageblocks.TextBlock',
              'pageblocks.HTMLBlock',
              'pageblocks.PullQuoteBlock',
              'pageblocks.ImageBlock',
              'pageblocks.ImagePullQuoteBlock',
              'quizblock.Quiz',
              'careermapblock.CareerMap',
              'fridgeblock.FridgeBlock',
              'likertblock.Questionnaire',
              ]

# these are by their display names for now
EPUB_ALLOWED_BLOCKS = [
    'Text Block', 'HTML Block', 'Pull Quote']

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

# WIND settings

AUTHENTICATION_BACKENDS = ('djangowind.auth.WindAuthBackend',
                           'django.contrib.auth.backends.ModelBackend',)
WIND_BASE = "https://wind.columbia.edu/"
WIND_SERVICE = "cnmtl_full_np"

SEED_STAND = "test.example.com"
