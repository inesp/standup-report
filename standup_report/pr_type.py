from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from enum import StrEnum
from typing import Self

logger = logging.getLogger(__name__)


class SafeStrEnum(StrEnum):
    @classmethod
    def from_string(cls, value: str | None) -> Self | None:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            return None


ONE_MIN = timedelta(seconds=60)
ONE_HOUR = timedelta(hours=1)
ONE_DAY = timedelta(days=1)


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
        now = datetime.now(UTC)
        diff = now - self.last_change

        if diff < ONE_MIN:
            return "just now"
        if diff < ONE_HOUR:
            return f"{int(diff / ONE_MIN)}m ago"
        if diff < ONE_DAY:
            return f"{int(diff / ONE_HOUR)}h ago"
        return f"{int(diff / ONE_DAY)}d ago"
