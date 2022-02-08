from django.urls import path

from .views import GroupListCreate, ProjectList, UserListCreate, UsernameViewSet, UserRetrieveUpdateDestroy

urlpatterns = [
    path('groups/', GroupListCreate.as_view()),
    path('projects/', ProjectList.as_view()),
    path('users/', UserListCreate.as_view()),
    path('users/username/<str:pk>', UsernameViewSet.as_view({'get': 'retrieve'})),
    path('users/<int:pk>/', UserRetrieveUpdateDestroy.as_view()),
]
