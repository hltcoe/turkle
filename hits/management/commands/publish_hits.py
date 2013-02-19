from django.core.management.base import BaseCommand, CommandError
import sys
from hits.models import Hit, HitTemplate


class Command(BaseCommand):

    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError('usage: python manage.py publish_hits TEMPLATE_FILE_PATH CSV_FILE_PATH')

        TEMPLATE_FILE_PATH, CSV_FILE_PATH = args

        with open(TEMPLATE_FILE_PATH) as fh:
            template = HitTemplate(
                    form=fh.read(),
                    source_file=TEMPLATE_FILE_PATH
            )
            template.save()

        with open(CSV_FILE_PATH) as fh:
            sys.stderr.write('Creating HITs')
            header = None
            for i, row in enumerate(fh.readlines()):
                if i == 0:
                    header = row.strip('\n')
                    continue
                hit = Hit(
                        source_file=TEMPLATE_FILE_PATH,
                        source_line=i + 1,
                        form=template,
                        input_csv_fields=header,
                        input_csv_values=row.strip('\n')
                )
                hit.save()
