import os, sys, site

# enable the virtualenv
site.addsitedir('/var/www/forest/forest/ve/lib/python2.6/site-packages')

# paths we might need to pick up the project's settings
sys.path.append('/var/www/')
sys.path.append('/var/www/forest/')
sys.path.append('/var/www/forest/forest/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'forest.settings_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
