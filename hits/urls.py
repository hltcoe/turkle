from django.conf.urls import patterns, url

urlpatterns = patterns('hits.views',
    url(r'^$', 'index'),
    url(r'^(?P<hit_id>\d+)/$', 'detail'),
    url(r'^(?P<hit_id>\d+)/results/$', 'results'),
    url(r'^(?P<hit_id>\d+)/submission/$', 'submission'),
)
