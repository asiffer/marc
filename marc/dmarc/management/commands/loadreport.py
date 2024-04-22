import os
from typing import List, Literal

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from pydantic import ValidationError

from marc.dmarc.management.commands._logging import logger
from marc.dmarc.parser import extract_parse, import_to_database


class Command(BaseCommand):
    help = "Import DMARC report (xml: raw, zipped or gzipped)"

    def add_arguments(self, parser):
        parser.add_argument("report", type=str, nargs="+")

    def handle(
        self,
        *args,
        report: List[str],
        verbosity: Literal[0, 1, 2, 3],
        **options,
    ):
        # see https://docs.python.org/3/library/logging.html#logging-levels
        logger.setLevel(40 - 10 * verbosity)

        total = 0
        for r in report:
            if os.path.isdir(r):
                continue

            try:
                with transaction.atomic():
                    with open(r, "rb") as f:
                        import_to_database(extract_parse(f))
                total += 1
                logger.debug(f"File {r} imported")
                # if verbosity >= 2:
                #     print(f"File {r} imported")
            except IntegrityError:
                logger.debug(f"File {r} already imported")
            except ValidationError as err:
                logger.error(err)

        logger.info(f"{total} report(s) imported")
