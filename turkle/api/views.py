from django.contrib.auth.models import Group, User
from rest_framework import viewsets

from ..models import Batch, Project
from .serializers import BatchSerializer, GroupSerializer, ProjectSerializer, UserSerializer


class BatchViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing batches.
    retrieve: Retrieve a batch as identified by id.
    create:   Create a new batch and return it.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing groups.
    retrieve: Retrieve a group as identified by id.
    create:   Create a new group and return it.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing projects.
    retrieve: Retrieve a project as identified by id.
    create:   Create a new project and return it.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    list:           Return a list of the existing users.
    retrieve:       Retrieve a user as identified by id.
    create:         Create a new user and return it.
    partial_update: Partial update one or more fields on a user (no checks for required fields).
    update:         Update fields on a user (required fields are checked).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
