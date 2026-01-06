from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import IntEnum
from enum import auto

from standup_report.date_utils import ago
from standup_report.enum_utils import SafeStrEnum


class LinearState(SafeStrEnum):
    # One of "triage", "backlog", "unstarted", "started", "completed", "canceled".
    STARTED = auto()
    COMPLETED = auto()
    CANCELED = auto()


class ActivityType(IntEnum):
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
class IssueActivity:
    title: str
    ident: str
    url: str
    activity_type: ActivityType
    state: LinearState | None
    activity_at: datetime
    pr_attachments: list[IssueAttachment] = field(default_factory=list)

    @property
    def activity(self) -> str:
        return self.activity_type.name

    @property
    def last_change_ago(self) -> str:
        return ago(self.activity_at)

    @property
    def pr_attachment_urls(self) -> set[str]:
        return {a.url for a in self.pr_attachments}
