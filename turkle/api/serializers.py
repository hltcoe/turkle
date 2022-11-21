import csv
import io
import re

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, User
from rest_framework import serializers

from ..models import Batch, Project
from ..utils import get_turkle_template_limit


class BatchSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    created_at = serializers.DateTimeField(read_only=True)
    filename = serializers.CharField(required=True)
    csv_text = serializers.CharField(required=True, write_only=True)
    active = serializers.BooleanField(default=True)
    published = serializers.BooleanField(default=True)
    login_required = serializers.BooleanField(default=True)
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = Batch
        fields = ['id', 'name', 'created_at', 'created_by', 'project', 'filename', 'csv_text',
                  'active', 'allotted_assignment_time', 'assignments_per_task', 'login_required',
                  'completed', 'published']

    def validate(self, attrs):
        if 'assignments_per_task' in attrs and not attrs['login_required'] and \
                attrs['assignments_per_task'] != 1:
            msg = "When login is not required to access the Project, " \
                  "the number of Assignments per Task must be 1"
            raise serializers.ValidationError({'assignments_per_task': msg})
        return attrs

    def create(self, validated_data):
        csv_text = validated_data.pop('csv_text')
        instance = super().create(validated_data)

        csv_fh = io.StringIO(csv_text)
        csv_fields = set(next(csv.reader(csv_fh)))
        csv_fh.seek(0)

        template_fields = set(instance.project.fieldnames)
        if csv_fields != template_fields:
            # should we error here? If so, move to validate
            # html interface sets a warning if this happens
            pass
        instance.create_tasks_from_csv(csv_fh)

        return instance


class GroupUsersField(serializers.ListField):
    child = serializers.IntegerField()

    def get_attribute(self, group):
        # Return group instance for to_representation()
        return group

    def to_representation(self, group):
        users = User.objects.filter(groups__id=group.id)
        return [user.id for user in users]

    def to_internal_value(self, data):
        # Returns the list of ids for create() to use
        return data


class GroupSerializer(serializers.ModelSerializer):
    users = GroupUsersField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'users']

    def create(self, validated_data):
        user_ids = validated_data.pop('users', [])
        group = super().create(validated_data)
        group.save()
        for user_id in user_ids:
            user = User.objects.get(id=user_id)
            user.groups.add(group.id)
        return group


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User object

    Required fields: username, password
    """
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

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        if 'password' in validated_data:
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
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    filename = serializers.CharField(required=True)
    active = serializers.BooleanField(default=True)
    login_required = serializers.BooleanField(default=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by',
                  'active', 'allotted_assignment_time', 'assignments_per_task', 'login_required',
                  'filename', 'html_template']

    def validate(self, attrs):
        # duplicate model validation as drf doesn't call model clean()
        # for a discussion on this see:
        # https://github.com/encode/django-rest-framework/discussions/7850
        # also, any validation that occurs after create() is called leaves
        # behind the object in the database so we do it all in this function
        if len(attrs['html_template']) > get_turkle_template_limit(True):
            raise serializers.ValidationError({'html_template': 'Template is too large'})
        if 'assignments_per_task' in attrs and not attrs['login_required'] and \
                attrs['assignments_per_task'] != 1:
            msg = "When login is not required to access the Project, " \
                  "the number of Assignments per Task must be 1"
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
