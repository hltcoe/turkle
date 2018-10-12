from django.conf.urls import url

from turkle.views import (
    accept_hit,
    accept_next_hit,
    download_batch_csv,
    expire_abandoned_assignments,
    hit_assignment,
    hit_assignment_iframe,
    index,
    preview,
    preview_iframe,
    preview_next_hit,
    return_hit_assignment,
    skip_and_accept_next_hit,
    skip_hit,
    update_auto_accept,
)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^expire_abandoned_assignments/$', expire_abandoned_assignments,
        name='expire_abandoned_assignments'),
    url(r'^update_auto_accept/$', update_auto_accept, name='update_auto_accept'),
    url(r'^(?P<hit_id>\d+)/$', preview, name='preview'),
    url(r'^(?P<hit_id>\d+)/iframe/$', preview_iframe, name='preview_iframe'),
    url(r'^(?P<hit_id>\d+)/assignment/(?P<hit_assignment_id>\d+)/return/$',
        return_hit_assignment, name='return_hit_assignment'),
    url(r'^(?P<hit_id>\d+)/assignment/(?P<hit_assignment_id>\d+)/$',
        hit_assignment, name='hit_assignment'),
    url(r'^(?P<hit_id>\d+)/assignment/iframe/(?P<hit_assignment_id>\d+)/$',
        hit_assignment_iframe, name='hit_assignment_iframe'),
    url(r'^batch/(?P<batch_id>\d+)/accept_hit/(?P<hit_id>\d+)/$', accept_hit, name='accept_hit'),
    url(r'^batch/(?P<batch_id>\d+)/skip_hit/(?P<hit_id>\d+)/$', skip_hit, name='skip_hit'),
    url(r'^batch/(?P<batch_id>\d+)/skip_and_accept_next_hit/(?P<hit_id>\d+)/'
        '(?P<hit_assignment_id>\d+)/$',
        skip_and_accept_next_hit, name='skip_and_accept_next_hit'),
    url(r'^batch/(?P<batch_id>\d+)/accept_next_hit/$', accept_next_hit, name='accept_next_hit'),
    url(r'^batch/(?P<batch_id>\d+)/preview_next_hit/$', preview_next_hit, name='preview_next_hit'),
    url(r'^batch/(?P<batch_id>\d+)/download/$', download_batch_csv, name='download_batch_csv'),
]
