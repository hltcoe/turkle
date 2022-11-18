from django.urls import path
from rest_framework import permissions
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer

from .views import BatchViewSet, GroupViewSet, ProjectViewSet, UserViewSet
from ..utils import get_site_name


schema_view = get_schema_view(
    title=get_site_name() + ' API',
    version='1.0',
    renderer_classes=[JSONOpenAPIRenderer],
    permission_classes=(permissions.AllowAny,),
    public=True
)

batch_list = BatchViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
batch_detail = BatchViewSet.as_view({
    'get': 'retrieve'
})
group_list = GroupViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
group_detail = GroupViewSet.as_view({
    'get': 'retrieve'
})
project_list = ProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
project_detail = ProjectViewSet.as_view({
    'get': 'retrieve'
})
user_list = UserViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
user_detail = UserViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'put': 'update'
})

urlpatterns = [
    path('schema.json', schema_view),
    path('batches/', batch_list, name='batch-list'),
    path('batches/<int:pk>', batch_detail, name='batch-detail'),
    path('groups/', group_list, name='group-list'),
    path('groups/<int:pk>/', group_detail, name='group-detail'),
    path('projects/', project_list, name='project-list'),
    path('projects/<int:pk>', project_detail, name='project-detail'),
    path('users/', user_list, name='user-list'),
    path('users/<int:pk>', user_detail, name='user-detail'),
]
