from enum import StrEnum
from typing import Self


class SafeStrEnum(StrEnum):
    @classmethod
    def from_string(cls, value: str | None) -> Self | None:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            return None
