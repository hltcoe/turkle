from django.urls import path
from rest_framework import permissions
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer

from .views import BatchListCreate, BatchRetrieve, GroupListCreate, GroupRetrieve, ProjectListCreate, ProjectRetrieve,\
    UserListCreate, UserRetrieveUpdate
from ..utils import get_site_name


schema_view = get_schema_view(
    title=get_site_name() + ' API',
    version='1.0',
    renderer_classes=[JSONOpenAPIRenderer],
    permission_classes=(permissions.AllowAny,),
    public=True
)

urlpatterns = [
    path('schema.json', schema_view),
    path('batches/', BatchListCreate.as_view(), name='batches-list-create'),
    path('batches/<int:pk>', BatchRetrieve.as_view(), name='batches-details'),
    path('groups/', GroupListCreate.as_view(), name='groups-list-create'),
    path('groups/<int:pk>', GroupRetrieve.as_view(), name='groups-details'),
    path('projects/', ProjectListCreate.as_view(), name='projects-list-create'),
    path('projects/<int:pk>', ProjectRetrieve.as_view(), name='projects-details'),
    path('users/', UserListCreate.as_view(), name='users-list-create'),
    path('users/<int:pk>', UserRetrieveUpdate.as_view(), name='users-details'),
]
