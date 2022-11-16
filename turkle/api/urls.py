from django.urls import path

from .views import BatchListCreate, BatchRetrieve, GroupListCreate, ProjectListCreate, ProjectRetrieve, UserListCreate,\
    UsernameViewSet, UserRetrieveUpdateDestroy

urlpatterns = [
    path('batches/', BatchListCreate.as_view(), name='batches-list-create'),
    path('batches/<int:pk>', BatchRetrieve.as_view(), name='batches-details'),
    path('groups/', GroupListCreate.as_view(), name='groups-list-create'),
    path('projects/', ProjectListCreate.as_view(), name='projects-list-create'),
    path('projects/<int:pk>', ProjectRetrieve.as_view(), name='projects-details'),
    path('users/', UserListCreate.as_view(), name='users-list-create'),
    path('users/username/<str:pk>', UsernameViewSet.as_view({'get': 'retrieve'}), name='users-username'),
    path('users/<int:pk>', UserRetrieveUpdateDestroy.as_view(), name='users-details'),
]
