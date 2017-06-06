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
    # These are all the fake hostnames used in forest's tests
    ALLOWED_HOSTS = [
        'fooble',
        'test.example.com',
        'cloned.example.com',
        'cloned.forest.ccnmtl.columbia.edu',
    ]

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
    'django.contrib.humanize',
]

TEMPLATES[0]['OPTIONS']['context_processors'].append(  # noqa
    'forest.main.views.context_processor',
)

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

SEED_STAND = "test.example.com"
