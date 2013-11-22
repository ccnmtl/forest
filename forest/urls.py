from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView
import forest.main.views as views
import os.path
admin.autodiscover()

site_media_root = os.path.join(os.path.dirname(__file__), "../media")

urlpatterns = patterns(
    '',
    (r'^_epub/$', 'forest.main.views.epub_exporter'),

    ('^accounts/', include('djangowind.urls')),
    (r'^admin/', include(admin.site.urls)),
    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^munin/total_stands/',
     'forest.main.views.total_stands'),
    (r'^munin/total_sections/',
     'forest.main.views.total_sections'),
    (r'^munin/total_standusers/',
     'forest.main.views.total_standusers'),
    (r'^munin/', include('munin.urls')),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^logout/$', 'django.contrib.auth.views.logout',
     {'next_page': '/'}),
    (r'^site_media/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': site_media_root}),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    (r'^_stand/$', views.EditStandView.as_view()),
    (r'^_stand/add/$', views.AddStandView.as_view()),
    (r'^_stand/users/$', views.StandUsersView.as_view()),
    (r'^_stand/users/(?P<id>\d+)/$', views.EditStandUserView.as_view()),
    (r'^_stand/users/add/$', views.StandAddUserView.as_view()),
    (r'^_stand/users/(?P<pk>\d+)/delete/$',
     views.DeleteStandUserView.as_view()),
    (r'^_stand/groups/$', views.StandGroupsView.as_view()),
    (r'^_stand/groups/add/$',
     'forest.main.views.stand_add_group'),
    (r'^_stand/groups/(?P<id>\d+)/$',
     'forest.main.views.edit_stand_group'),
    (r'^_stand/groups/(?P<id>\d+)/delete/$',
     'forest.main.views.delete_stand_group'),
    (r'^_stand/blocks/$',
     'forest.main.views.manage_blocks'),
    (r'^_stand/css/$', views.CSSView.as_view()),
    (r'^_stand/delete/$', views.DeleteStandView.as_view()),
    (r'^_stand/clone/$', 'forest.main.views.cloner'),
    (r'^_quiz/', include('quizblock.urls')),
    (r'^_careermap/', include('careermapblock.urls')),
    (r'^_fridge/', include('fridgeblock.urls')),
    ('_smoketest/', include('smoketest.urls')),
    (r'^_stats/$', TemplateView.as_view(template_name="main/stats.html")),
    (r'^edit/(?P<path>.*)$', views.EditView.as_view(),
     {}, 'edit-page'),
    (r'^instructor/(?P<path>.*)$', views.InstructorView.as_view()),
    (r'^(?P<path>.*)$', views.PageView.as_view()),
)
