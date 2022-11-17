from django.contrib.auth.models import Group, User
from rest_framework import generics

from ..models import Batch, Project
from .serializers import BatchSerializer, GroupSerializer, ProjectSerializer, UserSerializer


class BatchListCreate(generics.ListCreateAPIView):
    """
    get:
    Return a list of the existing batches.

    post:
    Publish a new batch of tasks.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchRetrieve(generics.RetrieveAPIView):
    """
    Retrieve details about a batch.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class GroupListCreate(generics.ListCreateAPIView):
    """
    get:
    Return a list of the existing groups.

    post:
    Create a new group.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupRetrieve(generics.RetrieveAPIView):
    """
    Retrieve a group.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ProjectListCreate(generics.ListCreateAPIView):
    """
    get:
    Return a list of the existing projects.

    post:
    Create a new project.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectRetrieve(generics.RetrieveAPIView):
    """
    Retrieve a project.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class UserListCreate(generics.ListCreateAPIView):
    """
    get:
    Return a list of the existing users.

    post:
    Create a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdate(generics.RetrieveUpdateAPIView):
    """
    get:
    Retrieve a user.

    patch:
    Update one or more fields on a user (no checks for required fields).

    put:
    Update fields on a user (required fields are checked).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
