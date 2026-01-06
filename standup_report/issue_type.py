from dataclasses import dataclass
from datetime import datetime
from enum import auto

from standup_report.date_utils import ago
from standup_report.enum_utils import SafeIntEnum


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
class Issue:
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
