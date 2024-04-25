import os
import socket
from functools import partial
from typing import List

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, F, Q

DEFAULT_MAX_LENGTH = 4096


def extract_paths(directories: str) -> List[str]:
    return [s.strip() for s in directories.split("\n") if s != ""]


def validate_directories(directories: str):
    for p in extract_paths(directories):
        if not os.path.exists(p):
            raise ValidationError(f"path '{p}' does not exist")


class HelpTextMixin:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        for field in self._meta.fields:
            # Create a string, get_FIELDNAME_help text
            method_name = "{0}_help_text".format(field.name)

            # We can use curry to create the method with a pre-defined argument
            curried_method = partial(self._get_help_text, field_name=field.name)

            # And we add this method to the instance of the class.
            setattr(self, method_name, curried_method)

    def _get_help_text(self, field_name) -> str | None:
        """Given a field name, return it's help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.help_text


class AlignmentType(models.TextChoices):
    R = "r"
    S = "s"


class DkimResultType(models.TextChoices):
    NONE = "none"
    PASS = "pass"
    FAIL = "fail"
    POLICY = "policy"
    NEUTRAL = "neutral"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


class DmarcResultType(models.TextChoices):
    PASS = "pass"
    FAIL = "fail"


class DispositionType(models.TextChoices):
    NONE = "none"
    QUARANTINE = "quarantine"
    REJECT = "reject"


class PolicyOverrideType(models.TextChoices):
    FORWARDED = "forwarded"
    SAMPLED_OUT = "sampled_out"
    TRUSTED_FORWARDER = "trusted_forwarder"
    MAILING_LIST = "mailing_list"
    LOCAL_POLICY = "local_policy"
    OTHER = "other"


class SpfDomainScope(models.TextChoices):
    HELO = "helo"
    MFROM = "mfrom"


class SpfResultType(models.TextChoices):
    NONE = "none"
    NEUTRAL = "neutral"
    PASS = "pass"
    FAIL = "fail"
    SOFTFAIL = "softfail"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


class Identifier(models.Model):
    envelope_to = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text="The envelope recipient domain.",
    )
    envelope_from = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text="RFC5321.MailFrom domain.",
    )
    header_from = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        help_text="The RFC5322.From domain.",
    )

    class Meta:
        unique_together = [("envelope_to", "envelope_from", "header_from")]


class PolicyPublished(HelpTextMixin, models.Model):
    """
    The DMARC policy that applied to the messages in the report
    See https://www.rfc-editor.org/rfc/rfc7489.html#section-6.3
    """

    domain = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text="The domain at which the DMARC record was found.",
    )
    adkim = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=AlignmentType.choices,
        blank=True,
        null=True,
        help_text=(
            "Indicates whether strict or relaxed DKIM Identifier Alignment mode is required by the Domain Owner. "
            "In relaxed mode, the Organizational Domains of both the DKIM-authenticated signing domain "
            "(taken from the value of the 'd=' tag in the signature) and that of the RFC5322 "
            "'From' domain must be equal if the identifiers are to be considered aligned. "
            "In strict mode, only an exact match between both of the Fully Qualified Domain Names "
            "(FQDNs) is considered to produce Identifier Alignment."
        ),
    )
    aspf = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=AlignmentType.choices,
        blank=True,
        null=True,
        help_text=(
            "Indicates whether strict or relaxed SPF Identifier Alignment mode is required by theDomain Owner. "
            "In relaxed mode, the [SPF]-authenticated domain and RFC5322 "
            "'From' domain must have the same Organizational Domain. "
            "In strict mode, only an exact DNS domain match is considered to produce Identifier Alignment."
        ),
    )
    p = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DispositionType.choices,
        help_text=(
            "Requested Mail Receiver policy. "
            "Indicates the policy to be enacted by the Receiver at the request of the Domain Owner. "
            "Policy applies to the domain queried and to subdomains, unless subdomain policy is explicitly described using the 'sp' tag. "
            "This tag is mandatory for policy records only, but not for third-party reporting records"
        ),
    )
    sp = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DispositionType.choices,
        blank=True,
        null=True,
        help_text=(
            "Requested Mail Receiver policy for all subdomains. "
            "Indicates the policy to be enacted by the Receiver at the request of the Domain Owner. "
            "It applies only to subdomains of the domain queried and not to the domain itself."
        ),
    )
    pct = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of messages from the Domain Owner's mail stream to which the DMARC policy is to be applied.",
    )
    fo = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text=(
            "Failure reporting options."
            "Provides requested options for generation of failure reports. "
            "Report generators MAY choose to adhere to the requested options. "
            "This tag's content MUST be ignored if a 'ruf' tag is not also specified."
        ),
    )
    np = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text=(
            "Requested Mail Receiver policy for non-existent subdomains. "
            "Indicates the policy to be enacted by the Receiver at the request of the Domain Owner. "
            "It applies only to non-existent subdomains of the domain queried and not to either "
            "existing subdomains or the domain itself."
        ),
    )

    class Meta:
        unique_together = [("domain", "adkim", "aspf", "p", "sp", "pct", "fo", "np")]


class Feedback(models.Model):
    version = models.DecimalField(decimal_places=4, max_digits=8, blank=True, null=True)
    # report_metadata = models.ForeignKey(ReportMetadata, on_delete=models.CASCADE)
    policy_published = models.ForeignKey(PolicyPublished, on_delete=models.CASCADE)

    def auth(self):
        dkim_pass = Q(record__auth_results__dkim__result=DkimResultType.PASS)
        spf_pass = Q(record__auth_results__spf__result=SpfResultType.PASS)

        return {
            "dkim": Feedback.objects.filter(id=self.id)
            .annotate(
                success=Count(
                    "record__auth_results",
                    filter=dkim_pass,
                ),
                total=Count("record__auth_results"),
            )
            .annotate(rate=100.0 * F("success") / F("total"))
            .first()
            .rate,
            "spf": Feedback.objects.filter(id=self.id)
            .annotate(
                success=Count("record__auth_results", filter=spf_pass),
                total=Count("record__auth_results"),
            )
            .annotate(rate=100.0 * F("success") / F("total"))
            .first()
            .rate,
        }

    def dmarc(self):
        spf_pass = Q(record__row__policy_evaluated__spf=DmarcResultType.PASS)
        dkim_pass = Q(record__row__policy_evaluated__dkim=DmarcResultType.PASS)

        q = (
            Feedback.objects.filter(id=self.id)
            .annotate(
                spf=Count(
                    "record__row__policy_evaluated",
                    filter=spf_pass,
                ),
                dkim=Count(
                    "record__row__policy_evaluated",
                    filter=dkim_pass,
                ),
                overall=Count(
                    "record__row__policy_evaluated",
                    filter=spf_pass | dkim_pass,
                ),
                total=Count("record__row__policy_evaluated"),
            )
            .annotate(
                spf_rate=100.0 * F("spf") / F("total"),
                dkim_rate=100.0 * F("dkim") / F("total"),
                overall_rate=100.0 * F("overall") / F("total"),
            )
            .first()
        )

        return {"dkim": q.dkim_rate, "spf": q.spf_rate, "overall": q.overall_rate}


class ReportMetadata(models.Model):
    org_name = models.CharField(max_length=DEFAULT_MAX_LENGTH)
    email = models.CharField(max_length=DEFAULT_MAX_LENGTH)
    extra_contact_info = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
    )
    report_id = models.CharField(max_length=DEFAULT_MAX_LENGTH, unique=True)
    # The time range in UTC covered by messages in this report,
    # specified in seconds since epoch.
    date_range_begin = models.DateTimeField()
    date_range_end = models.DateTimeField()

    error = models.JSONField()

    feedback = models.OneToOneField(
        Feedback,
        on_delete=models.CASCADE,
        related_name="report_metadata",
    )


class Record(models.Model):
    """
    This element contains all the authentication results that
    were evaluated by the receiving system for the given set of
    messages.
    """

    identifiers = models.ForeignKey(Identifier, on_delete=models.CASCADE)

    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name="record",
    )


class AuthResult(models.Model):
    """
    This element contains DKIM and SPF results, uninterpreted with respect to DMARC.
    There may be no DKIM signatures, or multiple DKIM signatures.
    There will always be at least one SPF result.
    """

    record = models.OneToOneField(
        Record,
        on_delete=models.CASCADE,
        related_name="auth_results",
    )


class DkimAuthResult(models.Model):
    """
    DKIM is an email authentication method designed
    to detect forged sender addresses in email (email spoofing),
    a technique often used in phishing and email spam.
    DKIM allows the receiver to check that an email that claimed to have come
    from a specific domain was indeed authorized by the owner of that domain.


    It achieves this by affixing a digital signature, linked to a domain name,
    to each outgoing email message. The recipient system can verify this by
    looking up the sender's public key published in the DNS. A valid signature
    also guarantees that some parts of the email (possibly including attachments)
    have not been modified since the signature was affixed.
    """

    domain = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        help_text="The 'd=' parameter in the signature.",
    )
    selector = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text="The 's=' parameter in the signature.",
    )
    result = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DkimResultType.choices,
        help_text="The DKIM verification result.",
    )
    human_result = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        blank=True,
        null=True,
        help_text="Any extra information (e.g., from Authentication-Results).",
    )

    auth_results = models.OneToOneField(
        AuthResult,
        on_delete=models.CASCADE,
        related_name="dkim",
    )


class SpfAuthResult(models.Model):
    """
    Sender Policy Framework (SPF) is an email authentication method which ensures
    the sending mail server is authorized to originate mail from the email sender's
    domain.
    This authentication only applies to the email sender listed in the "envelope from"
    field during the initial SMTP connection.
    """

    domain = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        help_text="The checked domain.",
    )
    scope = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=SpfDomainScope.choices,
        blank=True,
        null=True,
        help_text="The scope of the checked domain.",
    )
    result = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=SpfResultType.choices,
        help_text="The SPF verification result.",
    )

    auth_results = models.OneToOneField(
        AuthResult,
        on_delete=models.CASCADE,
        related_name="spf",
    )


class Row(models.Model):
    source_ip = models.GenericIPAddressField(help_text="The connecting IP.")
    count = models.IntegerField(help_text="The number of matching messages.")
    # policy_evaluated = models.OneToOneField(
    #     PolicyEvaluated,
    #     on_delete=models.CASCADE,
    #     related_name="row",
    #     help_text="The DMARC disposition applying to matching messages.",
    # )

    record = models.OneToOneField(
        Record,
        on_delete=models.CASCADE,
        related_name="row",
    )

    def domain(self):
        if self.source_ip:
            return cache.get_or_set(
                self.source_ip,
                socket.gethostbyaddr(self.source_ip)[0],
            )
        return None


class PolicyEvaluated(models.Model):
    """
    DMARC will check the consistency (in strict and/or relaxed mode) of the following three domain names:

    - The domain name for DMARC is the one from the From: field of the email (after @).
    - The domain name for DKIM is the one declared in the signature (d= field).
    - The domain name for SPF is the one from the SMTP MAIL FROM command.
    """

    disposition = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DispositionType.choices,
    )
    dkim = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DmarcResultType.choices,
    )
    spf = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=DmarcResultType.choices,
    )

    row = models.OneToOneField(
        Row,
        on_delete=models.CASCADE,
        related_name="policy_evaluated",
        help_text="The DMARC disposition applying to matching messages.",
    )

    def dmarc(self) -> bool:
        """
        DMARC passes when either SPF or DKIM is verified and aligned.
        DMARC can neither explicitly require SPF, nor explicitly require DKIM, nor both.
        """
        return self.dkim == DmarcResultType.PASS or self.spf == DmarcResultType.PASS


class PolicyOverrideReason(models.Model):
    """
    How do we allow report generators to include new
    classes of override reasons if they want to be more
    specific than "other"?
    """

    type_value = models.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        choices=PolicyOverrideType.choices,
        blank=True,
        null=True,
        help_text="Reasons that may affect DMARC disposition or execution thereof.",
    )
    comment = models.CharField(max_length=DEFAULT_MAX_LENGTH, blank=True, null=True)

    policy_evaluated = models.ForeignKey(
        PolicyEvaluated,
        on_delete=models.CASCADE,
        related_name="reason",
    )


class Config(models.Model):
    recursive = models.BooleanField(
        default=False,
        help_text="Look for DMARC reports recursively in directories",
    )
    directories = models.TextField(
        blank=True,
        null=True,
        validators=[validate_directories],
        help_text="List of directories to look for DMARC reports (one directory by line)",
    )

    def dirlist(self) -> List[str]:
        return [v.strip() for v in self.directories.split("\n") if v.strip() != ""]


def get_config() -> Config:
    config = Config.objects.first()
    if config is None:
        config = Config.objects.create()
    return config
