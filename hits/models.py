from django.db import models
from jsonfield import JSONField


class Hit(models.Model):
    """ Human Intelligence Task
    """
    title = models.CharField(max_length=100)
    description = models.TextField()
    awsmturk_template = models.ForeignKey('AwsMTurkTemplate')
    awsmturk_template_values = JSONField()


class AwsMTurkTemplate(models.Model):
    template = models.TextField()
