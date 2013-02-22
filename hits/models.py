import json
from django.db import models


class Hit(models.Model):
    """ Human Intelligence Task
    """
    source_file = models.TextField()
    source_line = models.IntegerField()
    completed = models.BooleanField(default=False)
    form = models.ForeignKey('HitTemplate')
    input_csv_fields = models.TextField()
    input_csv_values = models.TextField()
    answers = models.TextField(blank=True)

    def __unicode__(self):
       return 'HIT id:{}'.format(self.id)

    def results_to_dict(self):
        result = {}
        for k, v in json.loads(self.answers, 'utf-8').items():
            if k != 'csrfmiddlewaretoken':
                result[k] = v
        return result

    def inputs_to_dict(self):
        fields = self.input_csv_fields.split(',')
        values = self.input_csv_values.split(',')
        return {k: v for k, v in zip(fields, values)}

    def generate_form(self):
        fields_vals_map = self.inputs_to_dict()
        result = self.form.form
        for field in fields_vals_map.keys():
            result = result.replace(
                    r'${' + field + r'}',
                    fields_vals_map[field]
            )
        return result


class HitTemplate(models.Model):
    source_file = models.TextField()
    form = models.TextField()

    def __unicode__(self):
       return 'HIT Template: {}'.format(self.source_file)
