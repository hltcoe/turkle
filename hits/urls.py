from django.conf.urls import url

from hits.views import (
    accept_next_hit,
    detail,
    download_batch_csv,
    hit_assignment,
    index,
    submission,
)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^(?P<hit_id>\d+)/$', detail, name='detail'),
    url(r'^(?P<hit_id>\d+)/assignment/(?P<hit_assignment_id>\d+)/$',
        hit_assignment, name='hit_assignment'),
    url(r'^(?P<hit_id>\d+)/assignment/(?P<hit_assignment_id>\d+)/submission/$',
        submission, name='submission'),
    url(r'^batch/(?P<batch_id>\d+)/accept_next_hit/$', accept_next_hit, name='accept_next_hit'),
    url(r'^batch/(?P<batch_id>\d+)/download/$', download_batch_csv, name='download_batch_csv'),
]
