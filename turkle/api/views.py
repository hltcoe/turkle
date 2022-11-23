from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
import guardian.shortcuts
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
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
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    http_method_names = ['get', 'head', 'options', 'post']

    @action(detail=False, url_path=r'name/(?P<name>[\w\ ]+)', url_name='name')
    def retrieve_by_name(self, request, name):
        """
        Retrieve a list of groups by the name of the group.
        This is a list because group names are not unique.
        """
        groups = Group.objects.filter(name=name).order_by('id')
        page = self.paginate_queryset(groups)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProjectPagination(PageNumberPagination):
    """Page number pagination with small page sizes"""
    page_size = 20


class ProjectViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing projects.
    retrieve: Retrieve a project as identified by id.
    create:   Create a new project and return it.
    """
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options', 'post']
    pagination_class = ProjectPagination

    @action(methods=['get', 'post'], detail=True, url_path=r'permissions')
    def retrieve_permissions(self, request, pk):
        queryset = Project.objects.filter(id=pk)
        project = get_object_or_404(queryset)
        if request.method == 'GET':
            return self.get_custom_permissions(project)
        else:
            pass

    @staticmethod
    def get_custom_permissions(project):
        groups = [group.id for group in project.get_group_custom_permissions()]
        users = [user.id for user in project.get_user_custom_permissions()]
        return Response({'groups': groups, 'users': users})

    @staticmethod
    def add_custom_permissions(project, permissions):
        pass


class UserViewSet(viewsets.ModelViewSet):
    """
    list:           Return a list of the existing users.
    retrieve:       Retrieve a user as identified by id.
    create:         Create a new user and return it.
    partial_update: Partial update one or more fields on a user (no checks for required fields).
    update:         Update fields on a user (required fields are checked).
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    http_method_names = ['get', 'head', 'options', 'patch', 'post', 'put']

    @action(detail=False, url_path=r'username/(?P<username>\w+)', url_name='username')
    def retrieve_by_username(self, request, username):
        """
        Retrieve a user from a username string.
        """
        queryset = User.objects.filter(username=username)
        user = get_object_or_404(queryset)
        serializer = UserSerializer(user)
        return Response(serializer.data)
