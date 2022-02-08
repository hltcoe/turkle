from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import Project
from .serializers import GroupSerializer, ProjectSerializer, UserSerializer


class ProjectList(APIView):
    """
    List all snippets, or create a new snippet.
    """
    def get(self, request, format=None):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


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
