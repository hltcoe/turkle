from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.response import Response

from ..models import Project
from .serializers import GroupSerializer, ProjectSerializer, UserSerializer


class ProjectListCreate(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        self.serializer_class.turkle_exclude_fields = ['html_template']
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.serializer_class.turkle_exclude_fields = []
        return self.create(request, *args, **kwargs)


class GroupListCreate(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class UserListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UsernameViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        queryset = User.objects.filter(username=pk)
        user = get_object_or_404(queryset)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
