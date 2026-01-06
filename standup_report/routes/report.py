import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from operator import attrgetter

from flask import Blueprint
from flask import render_template

from standup_report import github
from standup_report import linear
from standup_report.issue_type import IssueActivity
from standup_report.issue_type import LinearState
from standup_report.pr_type import PR
from standup_report.pr_type import PRState
from standup_report.settings import get_settings

report_bp = Blueprint("report", __name__)
logger = logging.getLogger(__name__)


@report_bp.route("/report")
@report_bp.route("/report/<int:hours>")
def build_report(hours: int = 24) -> str:
    time_ago = datetime.now(UTC) - timedelta(hours=hours)

    my_latest_prs: list[PR] = list(github.fetch_authored_prs(time_ago))
    my_open_prs: list[PR] = list(github.fetch_authored_open_prs())

    # Ok, KAR RABIM JE: še 1 + list of items kaj sem še drugega delala, z ikono in tako

    # sort: first MERGED PRs, inside sort by last_change
    my_latest_prs = sorted(my_latest_prs, key=attrgetter("last_change"))
    my_latest_prs = sorted(
        my_latest_prs, key=lambda pr: pr.state == PRState.MERGED, reverse=True
    )

    my_linear_activity: list[IssueActivity] = list(linear.fetch_user_activity(time_ago))
    # We only want Linear activity that cannot be expressed in PRs. Because PRs are the most important.
    # So, we will exclude issues that have legit PRs.
    github_pr_urls: set[str] = {pr.url for pr in my_latest_prs}
    selected_linear_activity: list[IssueActivity] = [
        issue
        for issue in my_linear_activity
        if not issue.pr_attachment_urls.intersection(github_pr_urls)
    ]

    my_in_progress_issues: list[IssueActivity] = [
        issue for issue in my_linear_activity if issue.state == LinearState.STARTED
    ]

    return render_template(
        "report.html",
        title="Standup Report",
        subtitle=_build_subtitle(hours, time_ago),
        my_latest_prs=my_latest_prs,
        my_open_prs=my_open_prs,
        my_linear_activity=selected_linear_activity,
        my_in_progress_issues=my_in_progress_issues,
        since=time_ago,
        hours=hours,
        settings=get_settings(),
    )


ONE_DAY_HOURS = 24
ONE_WEEK_HOURS = 7 * 24


def _build_subtitle(hours: int, time_ago: datetime) -> str:
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
