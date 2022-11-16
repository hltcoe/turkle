from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.response import Response

from ..models import Batch, Project
from .serializers import BatchSerializer, GroupSerializer, ProjectSerializer, UserSerializer


class BatchListCreate(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchRetrieve(generics.RetrieveAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class GroupListCreate(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ProjectListCreate(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        self.serializer_class.turkle_exclude_fields = ['html_template']
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.serializer_class.turkle_exclude_fields = []
        return self.create(request, *args, **kwargs)


class ProjectRetrieve(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        self.serializer_class.turkle_exclude_fields = []
        return super().get(request, *args, **kwargs)


class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
