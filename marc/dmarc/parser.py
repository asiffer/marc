import gzip
import zipfile
from datetime import UTC, datetime
from io import BufferedReader
from typing import Any, Dict

from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from marc.dmarc.models import (
    AuthResult,
    DkimAuthResult,
    Feedback,
    Identifier,
    PolicyEvaluated,
    PolicyOverrideReason,
    PolicyPublished,
    Record,
    ReportMetadata,
    Row,
    SpfAuthResult,
)
from marc.report import Feedback as FeedbackDataclass

#     with open(file, "rb") as f:
#         return f.read(2) == b"\x1f\x8b"


# def is_zip(file: str | Path) -> bool:
#     with open(file, "rb") as f:
#         return f.read(2) == b"\x50\x4b"


# def parse_file(file: str | Path) -> FeedbackDataclass:
#     if is_gzip(file):
#         stream = StringIO(gzip.decompress(open(file, "rb").read()).decode())
#         return parse(stream)
#     if is_zip(file):
#         zf = zipfile.ZipFile(file)
#         f = zf.namelist()[0]
#         return parse(zf.open(f))
#     with open(file, "rb") as f:
#         return parse(file)


def extract_stream(stream: BufferedReader) -> BufferedReader:
    """Extract a stream if it is zipped or gzipped"""
    magic = stream.read(2)
    stream.seek(0)  # reset
    if magic == b"\x1f\x8b":  # gzip
        return gzip.GzipFile(fileobj=stream, mode="rb")
    elif magic == b"\x50\x4b":  # zip
        z = zipfile.ZipFile(stream)
        return z.open(z.namelist()[0])
    return stream


def parse(xml_stream: BufferedReader) -> FeedbackDataclass:
    """Read an XML report and return a Feedback object"""
    config = ParserConfig()
    context = XmlContext()
    xml_parser = XmlParser(context=context, config=config)
    return xml_parser.parse(xml_stream, FeedbackDataclass)


def extract_parse(stream: BufferedReader) -> FeedbackDataclass:
    return parse(extract_stream(stream))


def as_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__pydantic_serializer__"):
        return obj.__pydantic_serializer__.to_python(obj)
    raise ValueError(
        f"No pydantic serializer found. Ensure it is a pydantic dataclass:\n{obj}"
    )


def import_to_database(obj: FeedbackDataclass) -> Feedback:
    # create the policy
    policy_published, _ = PolicyPublished.objects.get_or_create(
        **as_dict(obj.policy_published)
    )

    # create the feedback
    feedback = Feedback.objects.create(
        # report_metadata=report_metadata,
        policy_published=policy_published,
        version=obj.version,
    )

    raw = as_dict(obj.report_metadata)
    # create date range
    date_range = raw.pop("date_range")
    ReportMetadata.objects.create(
        feedback=feedback,
        **raw,
        date_range_begin=datetime.fromtimestamp(date_range["begin"], tz=UTC),
        date_range_end=datetime.fromtimestamp(date_range["end"], tz=UTC),
    )

    for record in obj.record:
        # create identifiers
        identifiers, _ = Identifier.objects.get_or_create(**as_dict(record.identifiers))

        # create record
        rec = Record.objects.create(
            feedback=feedback,
            identifiers=identifiers,
        )

        # create auth_results
        auth_results = AuthResult.objects.create(record=rec)

        # spf results
        for spf in record.auth_results.spf:
            spf_r = as_dict(spf)
            SpfAuthResult.objects.create(**spf_r, auth_results=auth_results)

        # dkim results
        for dkim in record.auth_results.dkim:
            dkim_r = as_dict(dkim)
            DkimAuthResult.objects.create(**dkim_r, auth_results=auth_results)

        raw = as_dict(record.row)
        # create policy_evaluated
        pe = raw.pop("policy_evaluated")
        # create row
        row = Row.objects.create(**raw, record=rec)

        reason = pe.pop("reason")
        policy_evaluated = PolicyEvaluated.objects.create(**pe, row=row)
        for reason in reason:
            PolicyOverrideReason.objects.create(
                **reason,
                policy_evaluated=policy_evaluated,
            )
        # # create row
        # row = Row.objects.create(**raw, policy_evaluated=policy_evaluated)

    return feedback
