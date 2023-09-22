import io

from django.contrib.auth.models import Group, User
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from ..models import Batch, Project
from .serializers import BatchSerializer, BatchCustomPermissionsSerializer, GroupSerializer, \
    ProjectSerializer, ProjectCustomPermissionsSerializer, UserSerializer

"""
Note: DRF still requires regular expressions in URLs rather than Django path expressions
https://github.com/encode/django-rest-framework/issues/6148
"""


class BatchViewSet(viewsets.ModelViewSet):
    """
    list:     Return a list of the existing batches.
    retrieve: Retrieve a batch as identified by id.
    create:   Create a new batch and return it.
    partial_update: Update the name, active status or allotted assignment time for a batch.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    http_method_names = ['get', 'head', 'options', 'patch', 'post']

    @action(detail=True, methods=['post'], url_path=r'tasks', url_name='tasks')
    def add_tasks(self, request, pk):
        """
        Add new tasks to an existing batch.
        """
        queryset = Batch.objects.filter(id=pk)
        batch = get_object_or_404(queryset)
        csv_text = request.data.get('csv_text', None)
        if not csv_text:
            raise serializers.ValidationError({'csv_text': 'This field is required.'})
        BatchSerializer.validate_csv_fields(csv_text, batch.project)
        csv_fh = io.StringIO(csv_text)
        num_new_tasks = batch.create_tasks_from_csv(csv_fh)
        if num_new_tasks > 0 and batch.completed:
            batch.completed = False
            batch.save()
        return Response({'new_tasks': num_new_tasks}, status=status.HTTP_201_CREATED)

    @action(detail=True, url_path=r'results', url_name='download-results')
    def download_results(self, request, pk):
        """
        Download the current answers for this batch as a csv file.
        """
        queryset = Batch.objects.filter(id=pk)
        batch = get_object_or_404(queryset)
        filename = batch.csv_results_filename()
        csv_output = io.StringIO()
        batch.to_csv(csv_output, lineterminator='\n')
        csv_string = csv_output.getvalue()
        response = HttpResponse(csv_string, content_type='text/csv')
        response['Content-Length'] = len(csv_string)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, url_path=r'input', url_name='download-input')
    def download_input(self, request, pk):
        """
        Download the input csv for this batch.
        """
        queryset = Batch.objects.filter(id=pk)
        batch = get_object_or_404(queryset)
        csv_output = io.StringIO()
        batch.to_input_csv(csv_output, lineterminator='\n')
        csv_string = csv_output.getvalue()
        response = HttpResponse(csv_string, content_type='text/csv')
        response['Content-Length'] = len(csv_string)
        response['Content-Disposition'] = f'attachment; filename="{batch.filename}"'
        return response

    @action(detail=True, url_path=r'progress', url_name='progress')
    def progress(self, request, pk):
        """
        Get progress data for this batch.
        """
        queryset = Batch.objects.filter(id=pk)
        batch = get_object_or_404(queryset)
        return Response({
            'total_tasks': batch.total_tasks(),
            'total_task_assignments': batch.total_task_assignments(),
            'total_finished_tasks': batch.total_finished_tasks(),
            'total_finished_task_assignments': batch.total_finished_task_assignments()
        })


class BatchCustomPermissionsViewSet(viewsets.ViewSet):
    """
    get: Retrieve the current user and group permissions.
    post: Adds additional users or groups to permissions.
    put: Replaces user and group permissions.
    """
    serializer_class = BatchCustomPermissionsSerializer

    def list(self, request, batch_pk=None):
        """Retrieve the current user and group permissions."""
        queryset = Batch.objects.filter(id=batch_pk)
        batch = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=batch)
        return Response(serializer.data)

    def create(self, request, batch_pk=None):
        """Adds additional users or groups to permissions."""
        queryset = Batch.objects.filter(id=batch_pk)
        batch = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=batch, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.add(batch, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, batch_pk=None):
        """Adds additional users or groups to permissions."""
        queryset = Batch.objects.filter(id=batch_pk)
        batch = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=batch, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(batch, serializer.validated_data)
        return Response(serializer.data)


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
        if len(serializer.data) == 0:
            raise Http404()
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'], url_path=r'users', url_name='users')
    def add_users(self, request, pk):
        """
        Add users to a group. Payload is a dictionary with the key 'users' being a list.
        """
        queryset = Group.objects.filter(id=pk)
        group = get_object_or_404(queryset)
        new_user_ids = request.data.get('users', None)
        if not new_user_ids:
            raise serializers.ValidationError({'users': 'This field is required.'})
        try:
            users = [User.objects.get(id=user_id) for user_id in new_user_ids]
            for user in users:
                user.groups.add(group.id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'users': 'Unknown user id in list.'})
        return Response(GroupSerializer().to_representation(group))


class ProjectPagination(PageNumberPagination):
    """Page number pagination with small page sizes"""
    page_size = 20


class ProjectViewSet(viewsets.ModelViewSet):
    """
    list:           Return a list of the existing projects.
    retrieve:       Retrieve a project as identified by id.
    create:         Create a new project and return it.
    partial_update: Update one or more fields of a project.
    update:         Full update of project including all required fields.
    """
    queryset = Project.objects.all().order_by('id')
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'head', 'options', 'patch', 'post', 'put']
    pagination_class = ProjectPagination

    @action(detail=True, url_path=r'batches', url_name='batches')
    def batches(self, request, pk):
        """
        List batches for this project.
        """
        batches = Batch.objects.filter(project=pk).order_by('id')
        page = self.paginate_queryset(batches)
        # manually construct BatchSerializer here - copied from get_serializer()
        serializer_class = BatchSerializer
        kwargs = {'many': True}
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(page, **kwargs)
        if len(serializer.data) == 0:
            raise Http404()
        return self.get_paginated_response(serializer.data)


class ProjectCustomPermissionsViewSet(viewsets.ViewSet):
    """
    get: Retrieve the current user and group permissions.
    post: Adds additional users or groups to permissions.
    put: Replaces user and group permissions.
    """
    serializer_class = ProjectCustomPermissionsSerializer

    def list(self, request, project_pk=None):
        """Retrieve the current user and group permissions."""
        queryset = Project.objects.filter(id=project_pk)
        project = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=project)
        return Response(serializer.data)

    def create(self, request, project_pk=None):
        """Adds additional users or groups to permissions."""
        queryset = Project.objects.filter(id=project_pk)
        project = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=project, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.add(project, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, project_pk=None):
        """Adds additional users or groups to permissions."""
        queryset = Project.objects.filter(id=project_pk)
        project = get_object_or_404(queryset)
        serializer = self.serializer_class(instance=project, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(project, serializer.validated_data)
        return Response(serializer.data)


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
