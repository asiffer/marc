from typing import Literal

from django.core.management.base import BaseCommand

from marc.dmarc.management.commands._logging import logger
from marc.dmarc.models import Feedback, PolicyPublished


class Command(BaseCommand):
    help = "Remove all DMARC reports"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, verbosity: Literal[0, 1, 2, 3], **options):
        logger.setLevel(40 - 10 * verbosity)
        key = f"{Feedback._meta.app_label}.{Feedback.__name__}"
        _, results = Feedback.objects.all().delete()
        PolicyPublished.objects.all().delete()
        logger.info(f"{results.get(key, 0)} report(s) removed")
