from django.conf.urls import url

from hits.views import (
    index, detail, results, submission,
    download_batch_csv)

urlpatterns = [
    url(r'^$', index),
    url(r'^(?P<hit_id>\d+)/$', detail),
    url(r'^(?P<hit_id>\d+)/results/$', results),
    url(r'^(?P<hit_id>\d+)/submission/$', submission),
    url(r'^batch/(?P<batch_id>\d+)/download/$', download_batch_csv, name='download_batch_csv'),
]
