from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import ClassVar

from standup_report.ignore_mixin import IgnoreMixin
from standup_report.ignore_mixin import ItemType
from standup_report.note_utils import NoteMixin


@dataclass
class Calendar:
    title: str
    remote_id: str


@dataclass
class Meeting(IgnoreMixin, NoteMixin):
    title: str
    calendar: Calendar
    url: str
    remote_id: str
    start_time: datetime
    attendees: list[str] = field(default_factory=list)

    ignore_item_type: ClassVar[ItemType] = ItemType.MEETING

    @property
    def ignore_item_id(self) -> str:
        return self.remote_id

    @property
    def ignore_item_title(self) -> str:
        return self.title
