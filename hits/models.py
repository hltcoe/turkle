import os.path
import re
import sys

from django.contrib.auth.models import User
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


class HitAssignment(models.Model):
    class Meta:
        verbose_name = "HIT Assignment"

    answers = JSONField(blank=True)
    assigned_to = models.ForeignKey(User)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    hit = models.ForeignKey(Hit)
    updated_at = models.DateTimeField(auto_now=True)


class HitBatch(models.Model):
    class Meta:
        verbose_name = "HIT batch"
        verbose_name_plural = "HIT batches"

    assignments_per_hit = models.IntegerField(default=1)
    date_published = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=1024)
    hit_template = models.ForeignKey('HitTemplate')
    name = models.CharField(max_length=1024)

    def csv_results_filename(self):
        """Returns filename for CSV results file for this HitBatch
        """
        batch_filename, extension = os.path.splitext(os.path.basename(self.filename))

        # We are following Mechanical Turk's naming conventions for results files
        return "{}-Batch_{}_results{}".format(batch_filename, self.id, extension)

    def create_hits_from_csv(self, csv_fh):
        """
        Args:
            csv_fh (file-like object): File handle for CSV input

        Returns:
            Number of HITs created from CSV file
        """
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

        return num_created_hits

    def finished_hits(self):
        """
        Returns:
            QuerySet of all Hit objects associated with this HitBatch
            that have been completed.
        """
        return self.hit_set.filter(completed=True).order_by('-id')

    def total_finished_hits(self):
        return self.finished_hits().count()

    def total_hits(self):
        return self.hit_set.count()

    def to_csv(self, csv_fh):
        """Write CSV output to file handle for every Hit in batch

        Args:
            csv_fh (file-like object): File handle for CSV output
        """
        fieldnames, rows = self._results_data(self.finished_hits())
        writer = unicodecsv.DictWriter(csv_fh, fieldnames, quoting=unicodecsv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    def unfinished_hits(self):
        """
        Returns:
            QuerySet of all Hit objects associated with this HitBatch
            that have NOT been completed.
        """
        return self.hit_set.filter(completed=False).order_by('id')

    def _parse_csv(self, csv_fh):
        """
        Args:
            csv_fh (file-like object): File handle for CSV output

        Returns:
            A tuple where the first value is a list of strings for the
            header fieldnames, and the second value is an iterable
            that returns a list of values for the rest of the roww in
            the CSV file.
        """
        rows = unicodecsv.reader(csv_fh)
        header = rows.next()
        return header, rows

    def _get_csv_fieldnames(self, hits):
        """
        Args:
            hits (List of Hit objects):

        Returns:
            A tuple of strings specifying the fieldnames to be used in
            in the header of a CSV file.
        """
        input_field_set = set()
        answer_field_set = set()
        for hit in hits:
            input_field_set.update(hit.input_csv_fields.keys())
            answer_field_set.update(hit.answers.keys())
        return tuple(
            [u'Input.' + k for k in sorted(input_field_set)] +
            [u'Answer.' + k for k in sorted(answer_field_set)]
        )

    def _results_data(self, hits):
        """
        All completed HITs must come from the same template so that they have the
        same field names.

        Args:
            hits (List of Hit objects):

        Returns:
            A tuple where the first value is a list of fieldname strings, and
            the second value is a list of dicts, where the keys to these
            dicts are the values of the fieldname strings.
        """
        rows = []
        for hit in hits:
            row = {}
            row.update({u'Input.' + k: v for k, v in hit.input_csv_fields.items()})
            row.update({u'Answer.' + k: v for k, v in hit.answers.items()})
            rows.append(row)

        return self._get_csv_fieldnames(hits), rows

    def __unicode__(self):
        return 'HIT Batch: {}'.format(self.name)


class HitTemplate(models.Model):
    class Meta:
        verbose_name = "HIT template"

    assignments_per_hit = models.IntegerField(default=1)
    date_modified = models.DateTimeField(auto_now=True)
    filename = models.CharField(max_length=1024)
    form = models.TextField()
    name = models.CharField(max_length=1024)

    # Fieldnames are automatically extracted from form text
    fieldnames = JSONField(blank=True)

    def save(self, *args, **kwargs):
        # Extract fieldnames from form text, save fieldnames as keys of JSON dict
        unique_fieldnames = set(re.findall(r'\${(\w+)}', self.form))
        self.fieldnames = dict((fn, True) for fn in unique_fieldnames)
        super(HitTemplate, self).save(*args, **kwargs)

    def to_csv(self, csv_fh):
        """
        Writes CSV output to file handle for every Hit associated with template

        Args:
            csv_fh (file-like object): File handle for CSV output
        """
        batches = self.hitbatch_set.all()
        if batches:
            fieldnames = self._get_csv_fieldnames(batches)
            writer = unicodecsv.DictWriter(csv_fh, fieldnames, quoting=unicodecsv.QUOTE_ALL)
            writer.writeheader()
            for batch in batches:
                _, rows = batch._results_data(batch.finished_hits())
                for row in rows:
                    writer.writerow(row)

    def _get_csv_fieldnames(self, batches):
        """
        Args:
            batches (List of HitBatch objects)

        Returns:
            A tuple of strings specifying the fieldnames to be used in
            in the header of a CSV file.
        """
        input_field_set = set()
        answer_field_set = set()
        for batch in batches:
            for hit in batch.hit_set.all():
                input_field_set.update(hit.input_csv_fields.keys())
                answer_field_set.update(hit.answers.keys())
        return tuple(
            [u'Input.' + k for k in sorted(input_field_set)] +
            [u'Answer.' + k for k in sorted(answer_field_set)]
        )

    def __unicode__(self):
        return 'HIT Template: {}'.format(self.name)
