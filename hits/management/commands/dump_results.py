from django.core.management.base import BaseCommand, CommandError
import sys
from hits.models import Hit
from collections import defaultdict


def results_data(completed_hits):
    rows = []
    fieldnames = set()
    for hit in completed_hits:
        row = defaultdict(unicode)
        for k, v in hit.inputs_to_dict().items():
            #row[u'Input.' + k] = v.encode('latin-1').decode('utf-8')
            row['Input.' + k] = v
        for k, v in hit.results_to_dict().items():
            row['Answer.' + k] = v
        for k in row.keys():
            fieldnames.add(k)
        rows.append(row)
    return sorted(list(fieldnames)), rows


class Command(BaseCommand):

    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('usage: python manage.py dump_results RESULTS_TSV_FILE_PATH')
        RESULTS_TSV_FILE_PATH, = args

        completed_hits = Hit.objects.filter(completed=True)
        if not completed_hits.exists():
            sys.exit('There are no completed HITs.')

        fields, rows = results_data(completed_hits)
        with open(RESULTS_TSV_FILE_PATH, 'wb') as fh:
            fh.write('\t'.join(fields).encode('utf-8'))
            fh.write('\n')
            for row in rows:
                line = '\t'.join([row[k].replace('\t', ' ') for k in fields]) \
                        + '\n'
                fh.write(line.encode('utf-8'))
