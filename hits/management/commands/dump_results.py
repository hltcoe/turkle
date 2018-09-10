import os
import sys

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from hits.models import Hit, HitTemplate


class Command(BaseCommand):
    help = (
        'Dumps results of the completed HITs for the template'
        ' <template_file_path> to a file at <results_csv_file_path>. '
        ' If <template_file_path> is * then results will be written to'
        ' a separate file for each template and unique set of'
        ' fieldnames (<results_csv_file_path> will be interpreted as a'
        ' prefix for the individual results files).'
    )

    def add_arguments(self, parser):
        parser.add_argument('template_file_path', type=str)
        parser.add_argument('results_csv_file_path', type=str)

    def handle(self, *args, **options):
        template_file_path = options['template_file_path']
        results_csv_file_path = options['results_csv_file_path']

        if template_file_path == '*':
            results_idx = 0
            for template in HitTemplate.objects.all():
                # We dump HITs from all HIT batches
                completed_hits = Hit.objects.filter(completed=True).filter(hit_batch__hit_template=template)

                if completed_hits.exists():
                    real_results_path = '%s.%d.csv' % (
                        results_csv_file_path, results_idx
                    )
                    print 'Writing results for template %s to %s ...' % (
                        template.name, real_results_path
                    )
                    with open(real_results_path, 'wb') as fh:
                        template.to_csv(fh)

                    results_idx += 1

        else:
            template_file_path = os.path.abspath(template_file_path)

            try:
                template = HitTemplate.objects.get(name=template_file_path)
            except ObjectDoesNotExist:
                sys.exit('There is no matching <template_file_path>.')

            completed_hits = Hit.objects.filter(completed=True).filter(hit_batch__hit_template=template)
            if not completed_hits.exists():
                sys.exit('There are no completed HITs.')

            print 'Writing results for template %s to %s ...' % (
                template_file_path, results_csv_file_path
            )
            with open(results_csv_file_path, 'wb') as fh:
                template.to_csv(fh)
