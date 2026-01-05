from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from standup_report.date_utils import ago
from standup_report.enum_utils import SafeStrEnum

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
class OwnPR:
    number: int
    repo_slug: str
    title: str
    url: str
    created_at: datetime
    merged_at: datetime | None
    state: PRState
    last_change: datetime
    review_decision: PRReviewDecision | None

    @property
    def uid(self) -> str:
        return f"{self.repo_slug}/pull/{self.number}"

    @property
    def last_change_ago(self) -> str:
        return ago(self.last_change)
