import re
import sys

from django.db import models
from jsonfield import JSONField
import unicodecsv


# The default field size limit is 131072 characters
unicodecsv.field_size_limit(sys.maxsize)


class Hit(models.Model):
    """
    Human Intelligence Task
    """
    class Meta:
        verbose_name = "HIT"

    hit_batch = models.ForeignKey('HitBatch')
    completed = models.BooleanField(default=False)
    input_csv_fields = JSONField()
    answers = JSONField(blank=True)

    def __unicode__(self):
        return 'HIT id:{}'.format(self.id)

    def generate_form(self):
        result = self.hit_batch.hit_template.form
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


class HitBatch(models.Model):
    class Meta:
        verbose_name = "HIT batch"
        verbose_name_plural = "HIT batches"

    date_published = models.DateTimeField(auto_now_add=True)
    hit_template = models.ForeignKey('HitTemplate')
    filename = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024)

    def create_hits_from_csv(self, csv_fh):
        header, data_rows = self._parse_csv(csv_fh)

        num_created_hits = 0
        for row in data_rows:
            if not row:
                continue
            hit = Hit(
                hit_batch=self,
                input_csv_fields=dict(zip(header, row)),
            )
            hit.save()
            num_created_hits += 1

        sys.stderr.write('%d HITs created.\n' % num_created_hits)

    def finished_hits(self):
        return self.hit_set.filter(completed=True).order_by('-id')

    def unfinished_hits(self):
        return self.hit_set.filter(completed=False).order_by('id')

    def _parse_csv(self, csv_fh):
        rows = unicodecsv.reader(csv_fh)
        header = rows.next()
        return header, rows

    def __unicode__(self):
        return 'HIT Batch: {}'.format(self.name)


class HitTemplate(models.Model):
    class Meta:
        verbose_name = "HIT template"

    filename = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024)
    form = models.TextField()
    date_modified = models.DateTimeField(auto_now=True)

    # Fieldnames are automatically extracted from form text
    fieldnames = JSONField(blank=True)

    def save(self, *args, **kwargs):
        # Extract fieldnames from form text, save fieldnames as keys of JSON dict
        unique_fieldnames = set(re.findall(r'\${(\w+)}', self.form))
        self.fieldnames = dict((fn, True) for fn in unique_fieldnames)
        super(HitTemplate, self).save(*args, **kwargs)

    def __unicode__(self):
        return 'HIT Template: {}'.format(self.name)
