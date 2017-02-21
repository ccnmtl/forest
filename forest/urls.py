import django.contrib.auth.views
import django.views.static
import forest.main.views as views

from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = [
    url(r'^_epub/$', views.EpubExporterView.as_view()),

    url('^accounts/', include('djangowind.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^_impersonate/', include('impersonate.urls')),
    url(r'^pagetree/', include('pagetree.urls')),
    url(r'^logout/$', django.contrib.auth.views.logout, {'next_page': '/'}),
    url(r'^uploads/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),
    url(r'^_stand/$', views.EditStandView.as_view()),
    url(r'^_stand/add/$', views.AddStandView.as_view()),
    url(r'^_stand/users/$', views.StandUsersView.as_view()),
    url(r'^_stand/users/(?P<id>\d+)/$', views.EditStandUserView.as_view()),
    url(r'^_stand/users/add/$', views.StandAddUserView.as_view()),
    url(r'^_stand/users/(?P<pk>\d+)/delete/$',
        views.DeleteStandUserView.as_view()),
    url(r'^_stand/groups/$', views.StandGroupsView.as_view()),
    url(r'^_stand/groups/add/$', views.StandAddGroupView.as_view()),
    url(r'^_stand/groups/(?P<id>\d+)/$', views.EditStandGroupView.as_view()),
    url(r'^_stand/groups/(?P<pk>\d+)/delete/$',
        views.DeleteStandGroupView.as_view()),
    url(r'^_stand/blocks/$', views.ManageBlocksView.as_view()),
    url(r'^_stand/css/$', views.CSSView.as_view()),
    url(r'^_stand/delete/$', views.DeleteStandView.as_view()),
    url(r'^_stand/clone/$', views.ClonerView.as_view()),
    url(r'^_quiz/', include('quizblock.urls')),
    url(r'^_likert/', include('likertblock.urls')),
    url(r'^_careermap/', include('careermapblock.urls')),
    url(r'^_fridge/', include('fridgeblock.urls')),
    url('_smoketest/', include('smoketest.urls')),
    url(r'^_stats/$', TemplateView.as_view(template_name="main/stats.html")),
    url(r'^edit/(?P<path>.*)$', views.EditView.as_view(), {}, 'edit-page'),
    url(r'^instructor/(?P<path>.*)$', views.InstructorView.as_view()),
    url(r'^(?P<path>.*)$', views.PageView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
