from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView
import forest.main.views as views
admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^_epub/$', views.EpubExporterView.as_view()),

    ('^accounts/', include('djangowind.urls')),
    (r'^admin/', include(admin.site.urls)),
    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^logout/$', 'django.contrib.auth.views.logout',
     {'next_page': '/'}),
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
    (r'^_stand/groups/add/$', views.StandAddGroupView.as_view()),
    (r'^_stand/groups/(?P<id>\d+)/$', views.EditStandGroupView.as_view()),
    (r'^_stand/groups/(?P<pk>\d+)/delete/$',
     views.DeleteStandGroupView.as_view()),
    (r'^_stand/blocks/$', views.ManageBlocksView.as_view()),
    (r'^_stand/css/$', views.CSSView.as_view()),
    (r'^_stand/delete/$', views.DeleteStandView.as_view()),
    (r'^_stand/clone/$', views.ClonerView.as_view()),
    (r'^_quiz/', include('quizblock.urls')),
    (r'^_likert/', include('likertblock.urls')),
    (r'^_careermap/', include('careermapblock.urls')),
    (r'^_fridge/', include('fridgeblock.urls')),
    ('_smoketest/', include('smoketest.urls')),
    (r'^_stats/$', TemplateView.as_view(template_name="main/stats.html")),
    (r'^edit/(?P<path>.*)$', views.EditView.as_view(),
     {}, 'edit-page'),
    (r'^instructor/(?P<path>.*)$', views.InstructorView.as_view()),
    (r'^(?P<path>.*)$', views.PageView.as_view()),
)
