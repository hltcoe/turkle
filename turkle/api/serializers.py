from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import Project


class UserSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password',
                  'is_active', 'is_staff', 'is_superuser']

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class ProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = Project
        fields = ['id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by',
                  'active', 'allotted_assignment_time', 'assignments_per_task']
