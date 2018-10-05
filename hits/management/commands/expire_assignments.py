import logging

from django.core.management.base import BaseCommand

from hits.models import HitAssignment


class Command(BaseCommand):
    help = ()

    def handle(self, *args, **options):
        (total_deleted, _) = HitAssignment.expire_all_abandoned()
        logging.basicConfig(format="%(asctime)-15s %(message)s")
        logging.error('TURKLE: Expired {} abandoned Task Assignments'.format(total_deleted))
