from django.urls import path

from .views import ProjectList, UserListCreate, UserRetrieveUpdateDestroy

urlpatterns = [
    path('projects/', ProjectList.as_view()),
    path('users/', UserListCreate.as_view()),
    path('users/<int:pk>/', UserRetrieveUpdateDestroy.as_view()),
]
