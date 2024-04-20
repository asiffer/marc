from dataclasses import field
from decimal import Decimal
from enum import StrEnum
from typing import List, Optional


from pydantic import field_validator
from pydantic.dataclasses import dataclass


class AlignmentType(StrEnum):
    R = "r"
    S = "s"


class DkimresultType(StrEnum):
    NONE = "none"
    PASS = "pass"
    FAIL = "fail"
    POLICY = "policy"
    NEUTRAL = "neutral"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


class DmarcresultType(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class DateRangeType:
    begin: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    end: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


class DispositionType(StrEnum):
    NONE = "none"
    QUARANTINE = "quarantine"
    REJECT = "reject"


@dataclass
class IdentifierType:
    envelope_to: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    envelope_from: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    header_from: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


class PolicyOverrideType(StrEnum):
    FORWARDED = "forwarded"
    SAMPLED_OUT = "sampled_out"
    TRUSTED_FORWARDER = "trusted_forwarder"
    MAILING_LIST = "mailing_list"
    LOCAL_POLICY = "local_policy"
    OTHER = "other"


class SpfdomainScope(StrEnum):
    HELO = "helo"
    MFROM = "mfrom"


class SpfresultType(StrEnum):
    NONE = "none"
    NEUTRAL = "neutral"
    PASS = "pass"
    FAIL = "fail"
    SOFTFAIL = "softfail"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


@dataclass
class DkimauthResultType:
    class Meta:
        name = "DKIMAuthResultType"

    domain: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    selector: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    result: Optional[DkimresultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    human_result: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class PolicyOverrideReason:
    type_value: Optional[PolicyOverrideType] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    comment: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class PolicyPublishedType:
    domain: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    adkim: Optional[AlignmentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    aspf: Optional[AlignmentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    p: Optional[DispositionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    sp: Optional[DispositionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    pct: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    fo: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    np: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )

    @field_validator("sp", "fo", "np", mode="before")
    @classmethod
    def enum_or_none(cls, v):
        """ensure that if the field is a null string
        then we turn it into None
        """
        if v == "":
            return None
        return v


@dataclass
class ReportMetadataType:
    org_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    email: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    extra_contact_info: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    report_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    date_range: Optional[DateRangeType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    error: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class SpfauthResultType:
    class Meta:
        name = "SPFAuthResultType"

    domain: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    scope: Optional[SpfdomainScope] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    result: Optional[SpfresultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class AuthResultType:
    dkim: List[DkimauthResultType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    spf: List[SpfauthResultType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class PolicyEvaluatedType:
    disposition: Optional[DispositionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    dkim: Optional[DmarcresultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spf: Optional[DmarcresultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    reason: List[PolicyOverrideReason] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class RowType:
    source_ip: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"((1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]).){3}(1?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])|([A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}",
        },
    )
    count: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    policy_evaluated: Optional[PolicyEvaluatedType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RecordType:
    row: Optional[RowType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    identifiers: Optional[IdentifierType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    auth_results: Optional[AuthResultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class Feedback:
    class Meta:
        name = "feedback"

    version: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    report_metadata: Optional[ReportMetadataType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    policy_published: Optional[PolicyPublishedType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    record: List[RecordType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )
