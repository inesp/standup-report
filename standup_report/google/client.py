from __future__ import annotations

import logging

from standup_report.google.auth import get_credentials
from standup_report.remote.base_client import RESTResponse
from standup_report.remote.base_client import get_rest_response

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.googleapis.com/calendar/v3/"


def get_google_rest_response(path: str, params: dict | None = None) -> RESTResponse:
    assert not path.startswith("/")
    creds = get_credentials()
    return get_rest_response(
        full_url=f"{_BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {creds.token}",
        },
        params=params,
    )
