from django.conf.urls import url

from turkle.views import (
    accept_task,
    accept_next_task,
    task_assignment,
    task_assignment_iframe,
    index,
    preview,
    preview_iframe,
    preview_next_task,
    return_task_assignment,
    skip_and_accept_next_task,
    skip_task,
    stats,
    update_auto_accept,
)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^stats/$', stats, name='stats'),
    url(r'^update_auto_accept/$', update_auto_accept, name='update_auto_accept'),
    url(r'^task/(?P<task_id>\d+)/$', preview, name='preview'),
    url(r'^task/(?P<task_id>\d+)/iframe/$', preview_iframe, name='preview_iframe'),
    url(r'^task/(?P<task_id>\d+)/assignment/(?P<task_assignment_id>\d+)/return/$',
        return_task_assignment, name='return_task_assignment'),
    url(r'^task/(?P<task_id>\d+)/assignment/(?P<task_assignment_id>\d+)/$',
        task_assignment, name='task_assignment'),
    url(r'^task/(?P<task_id>\d+)/assignment/iframe/(?P<task_assignment_id>\d+)/$',
        task_assignment_iframe, name='task_assignment_iframe'),
    url(r'^batch/(?P<batch_id>\d+)/accept_task/(?P<task_id>\d+)/$',
        accept_task, name='accept_task'),
    url(r'^batch/(?P<batch_id>\d+)/skip_task/(?P<task_id>\d+)/$', skip_task, name='skip_task'),
    url(r'^batch/(?P<batch_id>\d+)/skip_and_accept_next_task/(?P<task_id>\d+)/' +
        r'(?P<task_assignment_id>\d+)/$',
        skip_and_accept_next_task, name='skip_and_accept_next_task'),
    url(r'^batch/(?P<batch_id>\d+)/accept_next_task/$', accept_next_task, name='accept_next_task'),
    url(r'^batch/(?P<batch_id>\d+)/preview_next_task/$',
        preview_next_task, name='preview_next_task'),
]
