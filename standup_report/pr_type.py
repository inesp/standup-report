from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from standup_report.date_utils import ago
from standup_report.enum_utils import SafeStrEnum
from standup_report.ignore_mixin import IgnoreMixin
from standup_report.ignore_mixin import ItemType

logger = logging.getLogger(__name__)


class PRState(SafeStrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MERGED = "MERGED"


class PRReviewDecision(SafeStrEnum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass
class PR(IgnoreMixin):
    number: int
    repo_slug: str
    title: str
    url: str
    created_at: datetime
    merged_at: datetime | None
    state: PRState
    last_change: datetime
    review_decision: PRReviewDecision | None

    issues: list[str] | None = None

    @property
    def uid(self) -> str:
        return f"{self.repo_slug}/pull/{self.number}"

    @property
    def last_change_ago(self) -> str:
        return ago(self.last_change)

    # Ignore properties
    ignore_item_type: ClassVar[ItemType] = ItemType.PR

    @property
    def ignore_item_id(self) -> str:
        return self.uid

    @property
    def ignore_item_title(self) -> str:
        return self.title
