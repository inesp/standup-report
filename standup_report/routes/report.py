import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from operator import attrgetter

from flask import Blueprint
from flask import render_template

from standup_report import duckdb_client
from standup_report import github
from standup_report import linear
from standup_report.ignore_mixin import ItemType
from standup_report.issue_type import Issue
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

    selected_linear_activity, selected_open_issues = _fetch_work_on_issues(
        time_ago, my_latest_prs, my_open_prs
    )

    all_done: list[PR | IssueActivity] = [
        *my_latest_prs,
        *selected_linear_activity,
    ]
    all_next: list[PR | Issue] = [
        *my_open_prs,
        *selected_open_issues,
    ]

    ignored_items: set[tuple[ItemType, str, str]] = duckdb_client.get_ignored_items()
    ignored_keys: set[tuple[ItemType, str]] = {
        (item_type, item_id) for item_type, item_id, _ in ignored_items
    }
    done_activity = [
        pr_or_issue
        for pr_or_issue in all_done
        if _get_item_key_for_ignoring(pr_or_issue) not in ignored_keys
    ]
    next_activity = [
        pr_or_issue
        for pr_or_issue in all_next
        if _get_item_key_for_ignoring(pr_or_issue) not in ignored_keys
    ]

    return render_template(
        "report.html",
        title="Standup Report",
        subtitle=_build_subtitle(hours, time_ago),
        done_activity=done_activity,
        next_activity=next_activity,
        ignored_items=ignored_items,
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


def _fetch_work_on_issues(
    time_ago: datetime, my_latest_prs: list[PR], my_open_prs: list[PR]
) -> tuple[list[IssueActivity], list[Issue]]:
    my_linear_activity: list[IssueActivity] = list(linear.fetch_user_activity(time_ago))
    # We only want Linear activity that cannot be expressed in PRs. Because PRs are the most important.
    # So, we will exclude issues that have legit PRs.
    github_pr_urls: set[str] = {pr.url for pr in my_latest_prs}
    selected_linear_activity: list[IssueActivity] = [
        issue
        for issue in my_linear_activity
        if not issue.pr_attachment_urls.intersection(github_pr_urls)
    ]

    my_open_issues: list[Issue] = list(linear.fetch_in_progress_issues())
    # Again: remove the ones with known PR
    github_open_pr_urls: set[str] = {pr.url for pr in my_open_prs}
    selected_open_issues: list[Issue] = [
        issue
        for issue in my_open_issues
        if not issue.pr_attachment_urls.intersection(github_open_pr_urls)
    ]

    # sort
    selected_open_issues = sorted(
        selected_open_issues, key=lambda issue: issue.state or 0, reverse=True
    )

    # If we have issues that are in-progress, then let's show only these, otherwise we'll show also todo-issues,
    # so, issues that aren't in the backlog, but they ARE put into the ToDo
    if (
        selected_open_issues
        and selected_open_issues[0].state
        and selected_open_issues[0].state >= LinearState.STARTED
    ):
        selected_open_issues = [
            i
            for i in selected_open_issues
            if i.state and i.state >= LinearState.STARTED
        ]

    return selected_linear_activity, selected_open_issues


def _get_item_key_for_ignoring(  # noqa: RET503
    pr_or_issue: PR | Issue,
) -> tuple[ItemType, str]:
    if isinstance(pr_or_issue, PR):
        return ItemType.PR, pr_or_issue.uid
    if isinstance(pr_or_issue, Issue):
        return ItemType.ISSUE, pr_or_issue.ident
