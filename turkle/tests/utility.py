import re

from turkle.models import Project, ProjectTemplate

def save_model(obj):
    """
    Imitates Django saving the model from a form.
    form.is_valid() calls clean methods including the model's full_clean
    See Django's forms/forms.py for details.
    """
    obj.full_clean(validate_unique=False)
    obj.save()

def create_project(name, html_template, login_required=True):
    unique_fieldnames = set(re.findall(r'\${(\w+)}', html_template))
    fieldnames = dict((fn, True) for fn in unique_fieldnames)
    project = Project.objects.create(name=name, login_required= login_required, fieldnames=fieldnames)
    ProjectTemplate.objects.create(
        project=project,
        html_template=html_template
    )
    return project
