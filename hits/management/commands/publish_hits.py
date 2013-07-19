import os
import sys
from django.core.management.base import BaseCommand, CommandError
from hits.models import Hit, HitTemplate
from unicodecsv import reader as UnicodeReader
#from util.unicodecsv import UnicodeReader
#from csv import reader as UnicodeReader


def get_or_create_template_from_html_file(htmlfile, template_file_path):
    template_file_path = os.path.abspath(template_file_path)
    name = template_file_path,
    form = htmlfile.read().decode('utf-8'),

    template, created = HitTemplate.objects.get_or_create(
        name=name,
        defaults={'form': form},
    )

    if created:
        template.save()

    return template


def parse_csv_file(fh):
    rows = UnicodeReader(fh)
    header = rows.next()
    return header, rows


class Command(BaseCommand):

    args = '<template_file_path> <csv_file_path>'
    help = (
        'Create a new HIT from each row of data in the CSV file based on the '
        'HTML HIT template.'
    )

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError(
                'usage: python manage.py publish_hits '
                '<template_file_path> '
                '<csv_file_path>'
            )

        template_file_path, csv_file_path = args

        with open(template_file_path, 'rb') as fh:
            template = get_or_create_template_from_html_file(
                fh,
                template_file_path
            )

        with open(csv_file_path, 'rb') as fh:
            sys.stderr.write('Creating HITs: ')
            header, data_rows = parse_csv_file(fh)
            i = 0
            for row in data_rows:
                hit = Hit(
                    source_file=csv_file_path,
                    source_line=i + 1,
                    form=template,
                    input_csv_fields=dict(zip(header, row)),
                )
                hit.save()
                i += 1
            sys.stderr.write('%d HITs created.\n' % i)