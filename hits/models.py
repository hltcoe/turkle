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
        pass

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
