from django.db import models
from jsonfield import JSONField


class Hit(models.Model):
    """
    Human Intelligence Task
    """
    completed = models.BooleanField(default=False)
    template = models.ForeignKey('HitTemplate')
    input_csv_fields = JSONField()
    answers = JSONField(blank=True)

    def __unicode__(self):
        return 'HIT id:{}'.format(self.id)

    def generate_form(self):
        result = self.template.form
        for field in self.input_csv_fields.keys():
            result = result.replace(
                r'${' + field + r'}',
                self.input_csv_fields[field]
            )

        # Surround the html in the form with two div tags:
        # one surrounding the HIT in a black box
        # and the other creating some white space between the black box and the
        # form.
        border = (
            '<div style="'
            ' width:100%%;'
            ' border:2px solid black;'
            ' margin-top:10px'
            '">'
            '%s'
            '</div>'
        )
        margin = '<div style="margin:10px">%s</div>'

        result = margin % result
        result = border % result
        return result

    def save(self, *args, **kwargs):
        if 'csrfmiddlewaretoken' in self.answers:
            del self.answers['csrfmiddlewaretoken']
        super(Hit, self).save(*args, **kwargs)


class HitTemplate(models.Model):
    name = models.CharField(max_length=256, unique=True)
    form = models.TextField()

    def __unicode__(self):
        return 'HIT Template: {}'.format(self.name)
