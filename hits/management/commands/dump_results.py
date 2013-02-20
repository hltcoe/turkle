from django.core.management.base import BaseCommand, CommandError
import csv
import sys
from hits.models import Hit


class Command(BaseCommand):

    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('usage: python manage.py dump_results RESULTS_CSV_FILE_PATH')
        RESULTS_CSV_FILE_PATH, = args

        completed_hits = Hit.objects.filter(completed=True)
        if not completed_hits.exists():
            sys.exit('There are no completed HITs.')

        rows = []
        fieldnames = set()
        for hit in completed_hits:
            row = {}
            for k, v in hit.inputs_to_dict().items():
                row['Input.' + k] = v.encode('utf8')
            for k, v in hit.results_to_dict().items():
                row['Answer.' + k] = v.encode('utf8')
            for k in row.keys():
                fieldnames.add(k)
            rows.append(row)

        with open(RESULTS_CSV_FILE_PATH, 'wb') as fh:
            writer = csv.DictWriter(
                    fh,
                    fieldnames,
                    restval='',
                    extrasaction='raise',
                    dialect='excel'
            )
            writer.writeheader()
            writer.writerows(rows)
