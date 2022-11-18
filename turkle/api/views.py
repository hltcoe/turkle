from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Batch, Project
from .serializers import BatchSerializer, GroupSerializer, ProjectSerializer, UserSerializer

"""
Note: DRF still requires regular expressions in URLs rather than Django path expressions
https://github.com/encode/django-rest-framework/issues/6148
"""


class BatchViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing batches.
    retrieve: Retrieve a batch as identified by id.
    create:   Create a new batch and return it.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    http_method_names = ['get', 'head', 'options', 'post']


class GroupViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing groups.
    retrieve: Retrieve a group as identified by id.
    create:   Create a new group and return it.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'head', 'options', 'post']


class ProjectViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing projects.
    retrieve: Retrieve a project as identified by id.
    create:   Create a new project and return it.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options', 'post']


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
    http_method_names = ['get', 'head', 'options', 'patch', 'post', 'put']

    @action(
        detail=False, url_path=r'username/(?P<username>\w+)', url_name='username')
    def retrieve_by_username(self, request, username):
        """
        Retrieve a user from a username string.
        """
        queryset = User.objects.filter(username=username)
        user = get_object_or_404(queryset)
        serializer = UserSerializer(user)
        return Response(serializer.data)
