import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Max, Min, Sum
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from marc.dmarc.forms import ConfigForm
from marc.dmarc.models import (
    Config,
    DispositionType,
    Feedback,
    Record,
    ReportMetadata,
    Row,
    get_config,
)
from marc.dmarc.parser import extract_parse, import_to_database

logger = logging.getLogger("django.marc")

__auth_results_background_colors__ = {
    "none": "#f1f5f9",
    "neutral": "#94a3b8",
    "pass": "#10b981",
    "fail": "#ef4444",
    "policy": "#06b6d4",
    "softfail": "#ec4899",
    "temperror": "#f97316",
    "permerror": "#f43f5e",
}

__disposition_background_colors__ = {
    DispositionType.NONE: "#10b981",
    DispositionType.QUARANTINE: "#f97316",
    DispositionType.REJECT: "#ef4444",
}


def _must_collect(p: Path, recursive: bool = False) -> int:
    if p.is_dir():
        return sum(_must_collect(p / f, recursive) for f in os.listdir(p))
    else:
        try:
            with open(p, "rb") as raw:
                with transaction.atomic():
                    import_to_database(extract_parse(raw))
            logger.info(f"{p} imported")
            return 1
        except IntegrityError as err:
            logger.debug(f"{p}: {err}")
        except BaseException as err:
            logger.error(f"{p}: {err}")

    return 0


class CollectView(TemplateView):
    http_method_names = ["get", "post"]
    template_name = "collect_button.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        config = get_config()
        total = sum(
            _must_collect(Path(d), recursive=config.recursive) for d in config.dirlist()
        )
        if total > 0:
            msg = f"{total} report(s) imported"
            messages.success(request, msg)
            logger.info(msg)
        elif total == 0:
            msg = "No new report added"
            messages.info(request, msg)
            logger.info(msg)
        return self.get(request=request)


class FragmentTemplateMixin:
    """Change the base template in case of HTMX request"""

    request: HttpRequest

    full_template = "base.html"
    fragment_template = "empty.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = super().get_context_data(**kwargs)
        is_htmx = self.request.headers.get("HX-Request", "false") == "true"
        if is_htmx:
            data["template_name"] = self.fragment_template
        else:
            data["template_name"] = self.full_template

        return data


class RecordListView(FragmentTemplateMixin, ListView):
    queryset = Record.objects.all().order_by(
        "-feedback__report_metadata__date_range_end"
    )
    context_object_name = "records"
    template_name = "record_list.html"


class RecordDetailView(FragmentTemplateMixin, DetailView):
    queryset = Record.objects.all()
    context_object_name = "record"
    template_name = "record.html"


class RecordRowView(DetailView):
    queryset = Record.objects.all()
    context_object_name = "record"
    template_name = "record_row.html"


class FeedbackListView(FragmentTemplateMixin, ListView):
    queryset = Feedback.objects.all().order_by("-report_metadata__date_range_end")
    context_object_name = "feedbacks"
    template_name = "feedback_list.html"


class FeedbackDetailView(FragmentTemplateMixin, DetailView):
    queryset = Feedback.objects.all()
    context_object_name = "feedback"
    template_name = "feedback.html"


class FeedbackRowView(DetailView):
    queryset = Feedback.objects.all()
    context_object_name = "feedback"
    template_name = "feedback_row.html"


class ConfigView(FragmentTemplateMixin, TemplateView):
    template_name = "config.html"


class ConfigUpdateView(UpdateView):
    form_class = ConfigForm
    template_name = "config_form.html"
    success_url = reverse_lazy("config-form")

    def get_object(self, *args, **kwargs) -> Config:
        return get_config()

    def get_form_kwargs(self) -> dict[str, Any]:
        return super().get_form_kwargs() | {"label_suffix": ""}


class FileView(TemplateView):
    template_name = "file_form.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        file = request.FILES["file"]
        try:
            obj = extract_parse(file.file)
            import_to_database(obj)
        except IntegrityError:
            msg = f"File {file} already imported"
            messages.warning(self.request, f"File {file} already imported")
            logger.warning(msg)
        except BaseException as err:
            messages.error(self.request, err.__str__())
            logger.error(err)

        return self.get(request)


class IndexView(FragmentTemplateMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        context_data["feedback"] = {"count": Feedback.objects.count()}
        context_data["record"] = {"count": Record.objects.count()}
        context_data["message"] = {
            "count": Row.objects.aggregate(total=Sum("count"))["total"]
        }
        context_data["disposition"] = {
            "labels": [d for d in DispositionType.values],
            "data": [
                Row.objects.filter(policy_evaluated__disposition=d).aggregate(
                    total=Sum("count")
                )["total"]
                for d in DispositionType.values
            ],
            "background_colors": [
                __disposition_background_colors__[d] for d in DispositionType.values
            ],
        }
        context_data["disposition_last30d"] = {
            "data": [
                Row.objects.filter(
                    policy_evaluated__disposition=d,
                    record__feedback__report_metadata__date_range_begin__gte=datetime.now(
                        UTC
                    )
                    - timedelta(days=7),
                ).aggregate(total=Sum("count"))["total"]
                for d in DispositionType.values
            ]
        }

        context_data["time"] = ReportMetadata.objects.all().aggregate(
            start=Min("date_range_begin"), end=Max("date_range_end")
        )
        return context_data
