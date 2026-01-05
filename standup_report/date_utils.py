from datetime import UTC
from datetime import datetime
from datetime import timedelta


def parse_str_to_date(date_str: str) -> datetime:
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)


def parse_optional_str_to_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)


def parse_datetime_to_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


ONE_MIN = timedelta(seconds=60)
ONE_HOUR = timedelta(hours=1)
ONE_DAY = timedelta(days=1)


def ago(dt: datetime) -> str:
    now = datetime.now(UTC)
    diff = now - dt

    if diff < ONE_MIN:
        return "just now"
    if diff < ONE_HOUR:
        return f"{int(diff / ONE_MIN)}m ago"
    if diff < ONE_DAY:
        return f"{int(diff / ONE_HOUR)}h ago"
    return f"{int(diff / ONE_DAY)}d ago"
