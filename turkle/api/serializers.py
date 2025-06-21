import csv
import io
import re

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, User
import guardian.shortcuts
from rest_framework import serializers

from ..models import Batch, Project
from ..utils import get_turkle_template_limit


class IntegerListField(serializers.ListField):
    child = serializers.IntegerField()


class CustomPermissionsSerializer(serializers.Serializer):
    users = IntegerListField()
    groups = IntegerListField()

    def to_representation(self, instance):
        groups = sorted([group.id for group in instance.get_group_custom_permissions()])
        users = sorted([user.id for user in instance.get_user_custom_permissions()])
        return {'groups': groups, 'users': users}

    def add(self, instance, validated_data):
        if not instance.custom_permissions:
            instance.custom_permissions = True
            instance.save()
        current_permissions = self.to_representation(instance)
        for user_id in validated_data['users']:
            if user_id not in current_permissions['users']:
                user = User.objects.get(id=user_id)
                guardian.shortcuts.assign_perm(self.perm_name, user, instance)
        for group_id in validated_data['groups']:
            if group_id not in current_permissions['groups']:
                group = Group.objects.get(id=group_id)
                guardian.shortcuts.assign_perm(self.perm_name, group, instance)

        return instance

    def create(self, validated_data):
        # required by serializer but replaced by add()
        pass

    def update(self, instance, validated_data):
        """replaces the current permissions"""
        # delete current permissions
        current_permissions = self.to_representation(instance)
        for user_id in current_permissions['users']:
            user = User.objects.get(id=user_id)
            guardian.shortcuts.remove_perm(self.perm_name, user, instance)
        for group_id in current_permissions['groups']:
            group = Group.objects.get(id=group_id)
            guardian.shortcuts.remove_perm(self.perm_name, group, instance)

        # create new ones
        if not instance.custom_permissions:
            instance.custom_permissions = True
            instance.save()
        for user_id in validated_data['users']:
            user = User.objects.get(id=user_id)
            guardian.shortcuts.assign_perm(self.perm_name, user, instance)
        for group_id in validated_data['groups']:
            group = Group.objects.get(id=group_id)
            guardian.shortcuts.assign_perm(self.perm_name, group, instance)

        return instance

    def validate(self, attrs):
        attrs['users'] = attrs.get('users', [])
        attrs['groups'] = attrs.get('groups', [])
        for user_id in attrs['users']:
            if not User.objects.filter(id=user_id).exists():
                raise serializers.ValidationError(
                    {'users': f'User with id {user_id} does not exist'}
                )
        for group_id in attrs['groups']:
            if not Group.objects.filter(id=group_id).exists():
                raise serializers.ValidationError(
                    {'groups': f'Group with id {group_id} does not exist'}
                )

        return attrs


class BatchSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    created_at = serializers.DateTimeField(read_only=True)
    filename = serializers.CharField(required=True)
    csv_text = serializers.CharField(required=True, write_only=True)
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Batch
        fields = ['id', 'name', 'created_at', 'created_by', 'project', 'filename', 'csv_text',
                  'allotted_assignment_time', 'assignments_per_task',
                  'login_required', 'custom_permissions',
                  'active', 'completed', 'published']

    def validate(self, attrs):
        if self.partial:
            # only allow certain attributes to be updated in a partial update
            allowed_keys = {'name', 'active', 'allotted_assignment_time'}
            illegal_keys = set(attrs.keys()).difference(allowed_keys)
            if illegal_keys:
                errors = {key: 'Cannot update through patch' for key in illegal_keys}
                raise serializers.ValidationError(errors)
            else:
                return attrs

        if 'login_required' not in attrs:
            attrs['login_required'] = attrs['project'].login_required
        if 'assignments_per_task' in attrs and attrs['assignments_per_task'] != 1 and \
                'login_required' in attrs and not attrs['login_required']:
            msg = "When login is not required to access the Batch, " \
                  "the number of Assignments per Task must be 1"
            raise serializers.ValidationError({'assignments_per_task': msg})

        self.validate_csv_fields(attrs['csv_text'], attrs['project'])

        return attrs

    @staticmethod
    def validate_csv_fields(csv_text, project):
        csv_fh = io.StringIO(csv_text)
        rows = csv.reader(csv_fh)
        header = next(rows)
        csv_fields = set(header)
        template_fields = set(project.fieldnames)
        if csv_fields != template_fields:
            template_but_not_csv = template_fields.difference(csv_fields)
            if template_but_not_csv:
                msg = 'The CSV file is missing fields that are in the HTML template. ' \
                      f'The missing fields are: {", ".join(template_but_not_csv)}'
                raise serializers.ValidationError({'csv_text': msg})

    def create(self, validated_data):
        # create tasks from CSV data and copy any custom permissions
        csv_text = validated_data.pop('csv_text')
        instance = super().create(validated_data)

        csv_fh = io.StringIO(csv_text)
        csv_fields = set(next(csv.reader(csv_fh)))
        csv_fh.seek(0)

        template_fields = set(instance.project.fieldnames)
        if csv_fields != template_fields:
            # Should we error here? If so, move to validate.
            # HTML interface sets a warning if this happens.
            pass
        instance.create_tasks_from_csv(csv_fh)

        if instance.project.custom_permissions:
            instance.custom_permissions = True
            instance.save()
            for user in instance.project.get_user_custom_permissions():
                guardian.shortcuts.assign_perm('can_work_on_batch', user, instance)
            for group in instance.project.get_group_custom_permissions():
                guardian.shortcuts.assign_perm('can_work_on_batch', group, instance)

        return instance


class BatchCustomPermissionsSerializer(CustomPermissionsSerializer):
    perm_name = 'can_work_on_batch'


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
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password',
                  'is_active', 'is_staff', 'is_superuser', 'date_joined', 'groups']

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


class ProjectBatchesField(serializers.ListField):
    child = serializers.IntegerField()

    def get_attribute(self, project):
        # Return group instance for to_representation()
        return project

    def to_representation(self, project):
        batches = Batch.objects.filter(project__id=project.id)
        return [batch.id for batch in batches]

    def to_internal_value(self, data):
        # Returns the list of ids for create() to use
        return data


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
    batches = ProjectBatchesField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by',
                  'active', 'allotted_assignment_time', 'assignments_per_task',
                  'login_required', 'custom_permissions',
                  'filename', 'html_template', 'batches']

    def validate(self, attrs):
        # This duplicates model validation as drf doesn't call model clean()
        # for a discussion on this see:
        # https://github.com/encode/django-rest-framework/discussions/7850
        # Also, any validation that occurs after create() is called leaves
        # behind the object in the database so we do it all in this function.
        # Finally, this needs to support create(), update(), and partial_update()
        # so we need to test if the attributes exist even if they are required.

        # if login is not required, can only have one assignment per task
        if self.partial and 'login_required' not in attrs:
            # set this so we can catch if user tries to set assignments_per_task incorrectly
            attrs['login_required'] = self.instance.login_required
        if 'assignments_per_task' in attrs and attrs['assignments_per_task'] != 1 and \
                'login_required' in attrs and not attrs['login_required']:
            msg = "When login is not required to access the Project, " \
                  "the number of Assignments per Task must be 1"
            raise serializers.ValidationError({'assignments_per_task': msg})

        if 'html_template' in attrs:
            if len(attrs['html_template']) > get_turkle_template_limit(True):
                raise serializers.ValidationError({'html_template': 'Template is too large'})

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

            attrs['html_template_has_submit_button'] =\
                bool(soup.select('input[type=submit], button[type=submit]'))

            # Extract fieldnames from html_template text, save fieldnames as keys of JSON dict
            unique_fieldnames = set(re.findall(r'\${(\w+)}', attrs['html_template']))
            attrs['fieldnames'] = dict((fn, True) for fn in unique_fieldnames)

        return attrs


class ProjectCustomPermissionsSerializer(CustomPermissionsSerializer):
    perm_name = 'can_work_on'
