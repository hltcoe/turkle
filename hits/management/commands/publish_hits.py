import os
import sys

from django.core.management.base import BaseCommand

from hits.models import HitBatch, HitTemplate


def get_or_create_template_from_html_file(htmlfile, template_file_path, template_name):
    template_file_path = os.path.abspath(template_file_path)
    filename = template_file_path
    if template_name:
        name = template_name
    else:
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


class Command(BaseCommand):
    help = (
        'Create a new HIT from each row of data in the CSV file based on the '
        'HTML HIT template.'
    )

    def add_arguments(self, parser):
        parser.add_argument('template_file_path', type=str)
        parser.add_argument('csv_file_path', type=str)
        parser.add_argument('--batch_name', type=str, default='')
        parser.add_argument('--template_name', type=str, default='')

    def handle(self, *args, **options):
        template_file_path = os.path.abspath(options['template_file_path'])
        csv_file_path = os.path.abspath(options['csv_file_path'])

        with open(template_file_path, 'rb') as fh:
            hit_template = get_or_create_template_from_html_file(
                fh,
                template_file_path,
                options['template_name'],
            )

        with open(csv_file_path, 'rb') as fh:
            sys.stderr.write('Creating HITs: ')
            if options['batch_name']:
                batch_name = options['batch_name']
            else:
                batch_name = csv_file_path
            hit_batch = HitBatch(
                hit_template=hit_template,
                filename=csv_file_path,
                name=batch_name
            )
            hit_batch.save()

            num_created_hits = hit_batch.create_hits_from_csv(fh)
            sys.stderr.write('%d HITs created.\n' % num_created_hits)
