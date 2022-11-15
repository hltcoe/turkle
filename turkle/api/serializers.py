import re

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, User
from rest_framework import serializers

from ..models import Project
from ..utils import get_turkle_template_limit


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
        # Optionally remove fields that shouldn't be serialized - set fields in view
        fields = super().get_fields()
        for field in self.turkle_exclude_fields:
            fields.pop(field, default=None)
        return fields

    def validate(self, attrs):
        # duplicate model validation as drf doesn't call model clean()
        # for a discussion on this see https://github.com/encode/django-rest-framework/discussions/7850
        # also, any validation that occurs after create() is called leaves behind the object in the database
        if len(attrs['html_template']) > get_turkle_template_limit(True):
            raise serializers.ValidationError({'html_template': 'Template is too large'})
        if 'assignments_per_task' in attrs and not attrs['login_required'] and attrs['assignments_per_task'] != 1:
            msg = "When login is not required to access the Project, the number of Assignments per Task must be 1"
            raise serializers.ValidationError({'assignments_per_task': msg})

        # This code is derived from process_template()
        # Matching mTurk we confirm at least one input, select, or textarea
        soup = BeautifulSoup(attrs['html_template'], 'html.parser')
        if soup.find('input') is None and soup.find('select') is None \
                and soup.find('textarea') is None:
            msg = "Template does not contain any fields for responses. " + \
                  "Please include at least one field (input, select, or textarea)." + \
                  "This usually means you are generating HTML with JavaScript." + \
                  "If so, add an unused hidden input."
            raise serializers.ValidationError({'html_template': msg})

        attrs['html_template_has_submit_button'] = bool(soup.select('input[type=submit]'))

        # Extract fieldnames from html_template text, save fieldnames as keys of JSON dict
        unique_fieldnames = set(re.findall(r'\${(\w+)}', attrs['html_template']))
        attrs['fieldnames'] = dict((fn, True) for fn in unique_fieldnames)

        return attrs
