from dataclasses import dataclass
from datetime import datetime
from enum import auto
from typing import ClassVar

from standup_report.date_utils import ago
from standup_report.enum_utils import SafeIntEnum
from standup_report.ignore_mixin import IgnoreMixin
from standup_report.ignore_mixin import ItemType
from standup_report.note_utils import NoteMixin


class LinearState(SafeIntEnum):
    # One of "triage", "backlog", "unstarted", "started", "completed", "canceled".
    UNSTARTED = auto()  # is "ToDo" state
    STARTED = auto()
    CANCELED = auto()
    COMPLETED = auto()


class ActivityType(SafeIntEnum):
    # These are sorted by importance.
    # Commenting is the least important. Issue completion is the most important.
    # We want to show only the most important action for every issue really...
    UNKNOWN = auto()
    COMMENTED = auto()
    CREATED = auto()
    CANCELED = auto()
    WORKED_ON = auto()
    COMPLETED = auto()


@dataclass
class IssueAttachment:
    url: str
    title: str
    last_updated: datetime

    @property
    def short_title(self) -> str:
        return self.title.split(":")[0]


@dataclass
class Issue(IgnoreMixin, NoteMixin):
    title: str
    ident: str
    url: str
    state: LinearState | None
    pr_attachments: list[IssueAttachment]

    @property
    def long_title(self) -> str:
        return f"{self.ident} {self.title}"

    @property
    def pr_attachment_urls(self) -> set[str]:
        return {a.url for a in self.pr_attachments}

    # Ignore properties
    ignore_item_type: ClassVar[ItemType] = ItemType.ISSUE

    @property
    def ignore_item_id(self) -> str:
        return self.ident

    @property
    def ignore_item_title(self) -> str:
        return self.title


@dataclass
class IssueActivity(Issue):
    activity_type: ActivityType
    activity_at: datetime

    @property
    def activity(self) -> str:
        return self.activity_type.name

    @property
    def last_change_ago(self) -> str:
        return ago(self.activity_at)
