import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import render_template

from standup_report import github
from standup_report.pr_type import OwnPR
from standup_report.settings import get_settings

report_bp = Blueprint("report", __name__)
logger = logging.getLogger(__name__)

@report_bp.route("/report")
@report_bp.route("/report/<int:hours>")
def build_report(hours: int = 24):
    time_ago = datetime.now(UTC) - timedelta(hours=hours)

    my_prs: list[OwnPR] = list(github.fetch_authored_prs(time_ago))

    return render_template(
        "report.html",
        title="Standup Report",
        subtitle=_build_subtitle(hours, time_ago),
        my_prs=my_prs,
        since=time_ago,
        hours=hours,
        settings=get_settings(),
    )


ONE_DAY_HOURS = 24
ONE_WEEK_HOURS = 7 * 24

def _build_subtitle(hours: int, time_ago: datetime)-> str:
    weeks = hours // ONE_WEEK_HOURS
    remaining_hours = hours % ONE_WEEK_HOURS
    days = remaining_hours // ONE_DAY_HOURS
    remaining_hours = remaining_hours % ONE_DAY_HOURS
    
    parts = []
    if weeks:
        parts.append(f"{weeks}w")
    if days:
        parts.append(f"{days}d")
    if remaining_hours:
        parts.append(f"{remaining_hours}h")
    
    time_label = " ".join(parts) if parts else "0h"
    return f"What I did in the last {time_label} (since: {time_ago.strftime('%Y-%m-%d %H:%M:%S UTC')})"
