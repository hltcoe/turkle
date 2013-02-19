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

    def generate_form(self):
        fields = self.input_csv_fields.split(',')
        values = self.input_csv_values.split(',')
        fields_vals_map = {k: v for k, v in zip(fields, values)}
        result = self.form.form
        for field in fields:
            result = result.replace(
                    r'${' + field + r'}',
                    fields_vals_map[field]
            )
        return result

    def result_to_dict(self):
        result = {}
        for kv in self.answers.split('&'):
            k, v = kv.split('=')
            result["Answer." + k] = v
        return result


class HitTemplate(models.Model):
    source_file = models.TextField()
    form = models.TextField()

    def __unicode__(self):
       return 'HIT Template: {}'.format(self.source_file)
