from django.conf.urls import url

from hits.views import (
    accept_next_hit,
    download_batch_csv,
    hit_assignment,
    hit_assignment_iframe,
    index,
)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^(?P<hit_id>\d+)/assignment/(?P<hit_assignment_id>\d+)/$',
        hit_assignment, name='hit_assignment'),
    url(r'^(?P<hit_id>\d+)/assignment/iframe/(?P<hit_assignment_id>\d+)/$',
        hit_assignment_iframe, name='hit_assignment_iframe'),
    url(r'^batch/(?P<batch_id>\d+)/accept_next_hit/$', accept_next_hit, name='accept_next_hit'),
    url(r'^batch/(?P<batch_id>\d+)/download/$', download_batch_csv, name='download_batch_csv'),
]
