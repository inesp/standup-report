from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from enum import StrEnum

logger = logging.getLogger(__name__)

ONE_MIN = timedelta(seconds=60)
ONE_HOUR = timedelta(hours=1)
ONE_DAY = timedelta(days=1)

class PRState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MERGED = "MERGED"


@dataclass
class OwnPR:
    number: int
    repo_slug: str
    title: str
    url: str
    author: str
    created_at: datetime
    merged_at: datetime | None
    state: PRState
    last_change: datetime

    @property
    def uid(self):
        return f"{self.repo_slug}/pull/{self.number}"

    @property
    def last_change_ago(self):
        now = datetime.now(UTC)
        diff = now - self.last_change

        if diff < ONE_MIN:
            return "just now"
        if diff < ONE_HOUR:
            return f"{int(diff / ONE_MIN)}m ago"
        if diff < ONE_DAY:
            return f"{int(diff / ONE_HOUR)}h ago"
        return f"{int(diff / ONE_DAY)}d ago"
