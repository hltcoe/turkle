from django.contrib.auth.models import Group, User
from rest_framework import serializers

from ..models import Project


class GroupUsernamesField(serializers.ListField):
    child = serializers.CharField()

    def get_attribute(self, group):
        # Return group instance for to_representation()
        return group

    def to_representation(self, group):
        users = User.objects.filter(groups__name=group.name)
        return [user.username for user in users]

    def to_internal_value(self, data):
        # Returns the list of usernames for create() to use
        return data


class GroupSerializer(serializers.ModelSerializer):
    users = GroupUsernamesField()

    class Meta:
        model = Group
        fields = ['name', 'users']

    def create(self, validated_data):
        usernames = validated_data.pop('users', [])
        group = super().create(validated_data)
        group.save()
        for username in usernames:
            user = User.objects.get(username=username)
            user.groups.add(group.id)
        return group


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User object

    Required fields: username, password
    """
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    is_active = serializers.BooleanField(default=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password',
                  'is_active', 'is_staff', 'is_superuser', 'groups']

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    updated_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    active = serializers.BooleanField(default=True)
    login_required = serializers.BooleanField(default=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by',
                  'active', 'allotted_assignment_time', 'assignments_per_task', 'login_required',
                  'html_template']

    def get_fields(self):
        # Optionally remove fields that shouldn't be serialized as set in view
        fields = super().get_fields()
        for field in self.turkle_exclude_fields:
            fields.pop(field, default=None)
        return fields
