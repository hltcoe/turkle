from datetime import datetime
import logging

from django.core.management.base import BaseCommand

from turkle.models import TaskAssignment


class Command(BaseCommand):
    help = ()

    def handle(self, *args, **options):
        t0 = datetime.now()
        (total_deleted, _) = TaskAssignment.expire_all_open()
        t = datetime.now()
        dt = (t - t0).total_seconds()
        logging.basicConfig(format="%(asctime)-15s %(message)s", level=logging.INFO)
        logging.info('TURKLE: Expired {0} open Task Assignments in {1:.3f} seconds'.
                     format(total_deleted, dt))
