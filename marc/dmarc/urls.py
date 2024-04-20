from django.urls import path
from django.views.decorators.cache import cache_page

from marc.dmarc.views import (
    CollectView,
    ConfigUpdateView,
    ConfigView,
    FeedbackDetailView,
    FeedbackListView,
    FeedbackRowView,
    FileView,
    IndexView,
    RecordDetailView,
    RecordListView,
    RecordRowView,
)

CACHE_TIMEOUT = 1

urlpatterns = [
    path(
        "",
        IndexView.as_view(),  # cache_page(CACHE_TIMEOUT)(IndexView.as_view()),
        name="index",
    ),
    path(
        "file/",
        FileView.as_view(),
        name="file",
    ),
    path(
        "collect/",
        CollectView.as_view(),
        name="collect",
    ),
    path(
        "config/",
        ConfigView.as_view(),
        name="config",
    ),
    path(
        "config/form/",
        ConfigUpdateView.as_view(),
        name="config-form",
    ),
    path(
        "feedback/",
        FeedbackListView.as_view(),
        name="feedback-list",
    ),
    path(
        "feedback/<int:pk>/",
        cache_page(CACHE_TIMEOUT)(FeedbackDetailView.as_view()),
        name="feedback-details",
    ),
    path(
        "feedback/<int:pk>/row/",
        cache_page(CACHE_TIMEOUT)(FeedbackRowView.as_view()),
        name="feedback-row",
    ),
    path(
        "record/",
        RecordListView.as_view(),
        name="record-list",
    ),
    path(
        "record/<int:pk>/",
        cache_page(CACHE_TIMEOUT)(RecordDetailView.as_view()),
        name="record-details",
    ),
    path(
        "record/<int:pk>/row/",
        cache_page(CACHE_TIMEOUT)(RecordRowView.as_view()),
        name="record-row",
    ),
]
