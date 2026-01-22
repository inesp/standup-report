import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
from datetime import datetime
from functools import partial

from standup_report.calendar_type import Calendar
from standup_report.calendar_type import Meeting
from standup_report.exceptions import RemoteException
from standup_report.google import client
from standup_report.google.client import get_google_rest_response
from standup_report.settings import get_settings

logger = logging.getLogger(__name__)

_MEETING_ACCEPTED = "accepted"
_MEETING_ACCEPTED_TENTATIVE = "tentative"


def get_calendar_events(time_min: datetime) -> list[Meeting]:
    """Fetch events from all calendars in parallel."""
    logger.info("---------- Fetching Google meetings")

    now = datetime.now(tz=UTC)
    calendars = fetch_all_calendars()
    event_fetching_fn = partial(
        _fetch_events_for_calendar,
        time_min=time_min.isoformat(),
        time_max=now.isoformat(),
    )

    with ThreadPoolExecutor() as executor:
        results = executor.map(
            event_fetching_fn,
            calendars,
        )

    all_calendar_events = []
    for meetings in results:
        all_calendar_events.extend(meetings)

    return all_calendar_events


def _fetch_events_for_calendar(
    cal: Calendar, *, time_min: str, time_max: str
) -> list[Meeting]:
    logger.debug(f"Fetching events from calendar {cal}")
    try:
        response = get_google_rest_response(
            path=f"calendars/{cal.remote_id}/events",
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
    except RemoteException:
        logger.error(f"Error fetching events from calendar {cal}")
        return []

    meetings = []
    for raw_event in response.data.get("items", []):
        title: str = raw_event["summary"]
        if title in get_settings().GOOGLE.IGNORED_MEETINGS:
            logger.warning(f"Ignoring meeting {title=}")
            continue

        start = raw_event["start"]
        if "dateTime" in start:
            start_time = datetime.fromisoformat(start["dateTime"])
        else:
            start_time = datetime.strptime(start["date"], "%Y-%m-%d")

        meeting = Meeting(
            title=raw_event["summary"],
            calendar=cal,
            url=raw_event["htmlLink"],
            remote_id=raw_event["id"],
            start_time=start_time,
            attendees=[
                att["email"]
                for att in raw_event.get("attendees", [])
                if att["responseStatus"]
                in (_MEETING_ACCEPTED, _MEETING_ACCEPTED_TENTATIVE)
                and not att.get("self")
            ],
        )
        logger.info(f"Found {raw_event=}")
        meetings.append(meeting)
    return meetings


def fetch_all_calendars() -> list[Calendar]:
    rest_url = "users/me/calendarList"
    google_response: dict = client.get_google_rest_response(path=rest_url).data
    raw_items: list[dict] = google_response.get("items", [])
    calendars: list[Calendar] = []
    for raw_cal in raw_items:
        cal = Calendar(
            title=raw_cal["summary"],
            remote_id=raw_cal["id"],
        )
        if cal.title in get_settings().GOOGLE.IGNORED_CALENDARS:
            logger.warning(f"=========== Ignoring calendar {cal.title=}")
            continue
        calendars.append(cal)
    return calendars
