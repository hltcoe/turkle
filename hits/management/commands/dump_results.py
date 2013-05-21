from django.core.management.base import BaseCommand, CommandError
import sys
from hits.models import Hit
from collections import defaultdict


def results_data(completed_hits):
    rows = []
    fieldnames = set()
    for hit in completed_hits:
        row = defaultdict(unicode)
        for k, v in hit.input_csv_fields.items():
            row[u'Input.' + k] = v
        for k, v in hit.answers.items():
            row[u'Answer.' + k] = v
        for k in row.keys():
            fieldnames.add(k)
        rows.append(row)
    return sorted(list(fieldnames)), rows


class Command(BaseCommand):

    args = '<results_tsv_file_path>'
    help = 'Dumps results of the completed HITs to a CSV file'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError(
                'usage: python manage.py dump_results <results_tsv_file_path>'
            )
        results_tsv_file_path, = args

        completed_hits = Hit.objects.filter(completed=True)
        if not completed_hits.exists():
            sys.exit('There are no completed HITs.')

        fields, rows = results_data(completed_hits)
        with open(results_tsv_file_path, 'wb') as fh:
            fh.write('\t'.join(fields).encode('utf-8'))
            fh.write('\n')
            for row in rows:
                line = (
                    '\t'.join(
                        [row[k].replace('\t', ' ') for k in fields]
                    ) + '\n'
                )
                fh.write(line.encode('utf-8'))
