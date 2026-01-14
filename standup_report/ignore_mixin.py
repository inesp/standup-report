from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from standup_report.enum_utils import SafeStrEnum


class ItemType(SafeStrEnum):
    PR = "PR"
    ISSUE = "Issue"


@dataclass
class IgnoreMixin(ABC):
    ignore_item_type: ClassVar[ItemType]

    @property
    @abstractmethod
    def ignore_item_id(self) -> str: ...

    @property
    @abstractmethod
    def ignore_item_title(self) -> str: ...
