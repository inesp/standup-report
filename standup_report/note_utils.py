from abc import ABC
from dataclasses import dataclass
from dataclasses import field

from standup_report.enum_utils import SafeStrEnum


class NoteCategory(SafeStrEnum):
    DONE = "done"
    NEXT = "next"


@dataclass
class NoteMixin(ABC):  # noqa: B024
    note: str = field(default="", kw_only=True)
