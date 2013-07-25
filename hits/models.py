from django.db import models
from jsonfield import JSONField


class Hit(models.Model):
    """
    Human Intelligence Task
    """
    completed = models.BooleanField(default=False)
    form = models.ForeignKey('HitTemplate')
    input_csv_fields = JSONField()
    answers = JSONField(blank=True)

    def __unicode__(self):
        return 'HIT id:{}'.format(self.id)

    def generate_form(self):
        result = self.form.form
        for field in self.input_csv_fields.keys():
            result = result.replace(
                r'${' + field + r'}',
                self.input_csv_fields[field]
            )
        return result

    def save(self):
        if 'csrfmiddlewaretoken' in self.answers:
            del self.answers['csrfmiddlewaretoken']
        super(Hit, self).save()


class HitTemplate(models.Model):
    name = models.CharField(max_length=256, unique=True)
    form = models.TextField()

    def __unicode__(self):
        return 'HIT Template: {}'.format(self.name)
