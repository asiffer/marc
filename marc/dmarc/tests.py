import os
from pathlib import Path
from typing import List

from django.test import Client, TestCase
from django.urls import reverse

from marc.dmarc.models import Config, Feedback, PolicyPublished
from marc.dmarc.parser import extract_parse, import_to_database

TEST_DIR = Path(__file__).parent.parent.parent / "tests"
DATA_DIR = TEST_DIR / "data"
TEST_FILES = [DATA_DIR / file for file in os.listdir(DATA_DIR)]


def import_all_test_files() -> List[Feedback]:
    out = []
    for file in TEST_FILES:
        with open(file, "rb") as f:
            out.append(import_to_database(extract_parse(f)))
    return out


class TestStringListField(TestCase):
    def test_io(self):
        # value = "\n".join(os.listdir("/"))
        a = Config.objects.create(directories="\n".join(os.listdir("/")))
        # a.refresh_from_db()
        print(a.directories)
        b = Config.objects.create(directories=os.listdir("/"))
        print(b.directories)
        # print(c.directories, type(c.directories))


class TestParser(TestCase):
    files = [DATA_DIR / file for file in os.listdir(DATA_DIR)]

    def test_parser(self):
        import_all_test_files()

    def test_import_to_database(self):
        before = Feedback.objects.count()
        import_all_test_files()
        after = Feedback.objects.count()

        assert (
            len(self.files) == after - before
        ), f"bad number of feedbacks: {len(self.files)} != {after - before}"

    def test_policy_published(self):
        Feedback.objects.all().delete()
        before = PolicyPublished.objects.count()
        import_all_test_files()
        after = PolicyPublished.objects.count()

        assert (
            after - before == 6
        ), f"bad number of policy published: {after - before} != 6"


class TestViews(TestCase):
    files = [DATA_DIR / file for file in os.listdir(DATA_DIR)]
    feedbacks: List[Feedback] = []

    def setUp(self) -> None:
        self.feedbacks = import_all_test_files()
        return super().setUp()

    def test_feedback(self):
        client = Client()
        res = client.get(reverse("feedback-details", args=(self.feedbacks[0].id,)))
        print(res)
