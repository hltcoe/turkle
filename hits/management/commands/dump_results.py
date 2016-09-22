import os
import sys


from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from hits.models import HitTemplate
from unicodecsv import DictWriter


def results_data(completed_hits):
    """
    All completed HITs must come from the same template so that they have the
    same field names.
    """
    fieldnames = sorted(
        [u'Input.' + k for k in completed_hits[0].input_csv_fields.keys()]
        + [u'Answer.' + k for k in completed_hits[0].answers.keys()]
    )

    rows = []
    for hit in completed_hits:
        row = {}
        row.update({u'Input.' + k: v for k, v in hit.input_csv_fields.items()})
        row.update({u'Answer.' + k: v for k, v in hit.answers.items()})
        rows.append(row)

    return fieldnames, rows


class Command(BaseCommand):
    help = (
        'Dumps results of the completed HITs for the template '
        '<template_file_path> '
        'to a file at <results_csv_file_path>'
    )

    def add_arguments(self, parser):
        parser.add_argument('template_file_path', type=str)
        parser.add_argument('results_csv_file_path', type=str)

    def handle(self, *args, **options):
        template_file_path = os.path.abspath(options['template_file_path'])
        results_csv_file_path = os.path.abspath(
            options['results_csv_file_path'])

        try:
            template = HitTemplate.objects.get(name=template_file_path)
        except ObjectDoesNotExist:
            sys.exit('There is no matching <template_file_path>.')

        completed_hits = template.hit_set.filter(completed=True)
        if not completed_hits.exists():
            sys.exit('There are no completed HITs.')

        fieldnames, rows = results_data(completed_hits)
        with open(results_csv_file_path, 'wb') as fh:
            writer = DictWriter(fh, fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
