from django.conf.urls import url

from hits.views import index, detail, results, submission

urlpatterns = [
    url(r'^$', index),
    url(r'^(?P<hit_id>\d+)/$', detail),
    url(r'^(?P<hit_id>\d+)/results/$', results),
    url(r'^(?P<hit_id>\d+)/submission/$', submission),
]
