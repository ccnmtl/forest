from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
import os.path
admin.autodiscover()

site_media_root = os.path.join(os.path.dirname(__file__),"media")

urlpatterns = patterns('',
                       ('^accounts/',include('djangowind.urls')),
                       (r'^admin/(.*)', admin.site.root),
                       (r'^munin/',include('munin.urls')),
                       (r'^pagetree/',include('pagetree.urls')),
                       (r'^logout/$', 'django.contrib.auth.views.logout', {'next_page':'/'}),
                       (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': site_media_root}),
                       (r'^uploads/(?P<path>.*)$','django.views.static.serve',{'document_root' : settings.MEDIA_ROOT}),
                       (r'^_stand/$','main.views.edit_stand'),
                       (r'^_stand/css/$','main.views.css'),
                       (r'^edit/(?P<path>.*)$','forest.main.views.edit_page'),
                       (r'^instructor/(?P<path>.*)$','forest.main.views.instructor_page'),
                       (r'^(?P<path>.*)$','forest.main.views.page'),
                       
) 

