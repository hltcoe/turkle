from django.db import models
from jsonfield import JSONField


class Hit(models.Model):
    """ Human Intelligence Task
    """
    template = models.ForeignKey('AwsMTurkTemplate')
    template_values = JSONField()

    def __unicode__(self):
       return '{}:{}'.format(self.template.title, self.id)

class AwsMTurkTemplate(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    template = models.TextField()
