from django.urls import path

from .views import GroupListCreate, ProjectListCreate, UserListCreate, UsernameViewSet, UserRetrieveUpdateDestroy

urlpatterns = [
    path('groups/', GroupListCreate.as_view(), name='groups-list-create'),
    path('projects/', ProjectListCreate.as_view(), name='projects-list-create'),
    path('users/', UserListCreate.as_view(), name='users-list-create'),
    path('users/username/<str:pk>', UsernameViewSet.as_view({'get': 'retrieve'}), name='users-username'),
    path('users/<int:pk>', UserRetrieveUpdateDestroy.as_view(), name='users-details'),
]
