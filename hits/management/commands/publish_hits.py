import os
import sys
from django.core.management.base import BaseCommand
from hits.models import Hit, HitBatch, HitTemplate
from unicodecsv import reader as UnicodeReader
#from util.unicodecsv import UnicodeReader
#from csv import reader as UnicodeReader

# The default field size limit is 131072 characters
import unicodecsv
unicodecsv.field_size_limit(sys.maxsize)


def get_or_create_template_from_html_file(htmlfile, template_file_path):
    template_file_path = os.path.abspath(template_file_path)
    filename = template_file_path
    name = template_file_path
    form = htmlfile.read().decode('utf-8')

    template, created = HitTemplate.objects.get_or_create(
        filename=filename,
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
    help = (
        'Create a new HIT from each row of data in the CSV file based on the '
        'HTML HIT template.'
    )

    def add_arguments(self, parser):
        parser.add_argument('template_file_path', type=str)
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        template_file_path = os.path.abspath(options['template_file_path'])
        csv_file_path = os.path.abspath(options['csv_file_path'])


        with open(template_file_path, 'rb') as fh:
            hit_template = get_or_create_template_from_html_file(
                fh,
                template_file_path
            )

        with open(csv_file_path, 'rb') as fh:
            sys.stderr.write('Creating HITs: ')
            hit_batch = HitBatch(
                hit_template=hit_template,
                filename=csv_file_path,
                name=csv_file_path
            )
            hit_batch.save()

            header, data_rows = parse_csv_file(fh)

            num_created_hits = 0
            for row in data_rows:
                if not row:
                    continue
                hit = Hit(
                    hit_batch=hit_batch,
                    input_csv_fields=dict(zip(header, row)),
                )
                hit.save()
                num_created_hits += 1

        sys.stderr.write('%d HITs created.\n' % num_created_hits)
