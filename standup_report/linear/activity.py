import logging
from datetime import UTC
from datetime import datetime
from operator import attrgetter
from typing import Literal

from standup_report.date_utils import parse_datetime_to_str
from standup_report.date_utils import parse_optional_str_to_date
from standup_report.date_utils import parse_str_to_date
from standup_report.dict_utils import safe_traverse
from standup_report.issue_type import ActivityType
from standup_report.issue_type import IssueActivity
from standup_report.issue_type import LinearState
from standup_report.remote.base_client import GQLResponse
from standup_report.remote.gql_utils import TAfterCursor
from standup_report.remote.gql_utils import THasMorePages
from standup_report.remote.gql_utils import extract_gql_query_from_file

from . import client

logger = logging.getLogger(__name__)


_COMMENTED_AT_KEY = "commented_at"


def fetch_user_activity(oldest_updated_at: datetime) -> list[IssueActivity]:
    logger.info(f"---------- Fetching Linear issue activity since {oldest_updated_at}.")
    authored_prs_query: str = extract_gql_query_from_file(
        "standup_report/linear/activity.graphql"
    )

    # Ideally, I'd get all the same data as is in
    #  Linear's MyIssues > Activity tab:
    #  1. issue created <- OK
    #  2. issue updated
    #  3. assigned issue state changed <- OK
    #  4. issue commented <- OK
    #  5. comment reacted
    #  6. opened pull request

    has_more_pages: THasMorePages = True

    activity_by_issue_id: dict[str, IssueActivity] = {}
    oldest_updated_at_str: str = parse_datetime_to_str(oldest_updated_at)

    while has_more_pages:
        one_page_response = client.post_linear_gql_query(
            query=authored_prs_query,
            variables={"email": "email@email.com", "gt_date": oldest_updated_at_str},
        )
        _process_one_page_of_actions(
            one_page_response, oldest_updated_at, activity_by_issue_id
        )
        has_more_pages, _ = _extract_page_info(one_page_response)

    sorted_desc_by_importance = sorted(
        activity_by_issue_id.values(), key=attrgetter("title")
    )
    sorted_desc_by_importance = sorted(
        sorted_desc_by_importance, key=attrgetter("activity_type"), reverse=True
    )

    return sorted_desc_by_importance


def _process_one_page_of_actions(
    response: GQLResponse,
    oldest_updated_at: datetime,
    activity_by_issue_id: dict[str, IssueActivity],
) -> None:

    # 1. issue created
    raw_created_issues = safe_traverse(response.data, "created_issues.nodes", [])
    _process_batch_of_issues(
        raw_created_issues,
        oldest_updated_at,
        activity_by_issue_id,
        activity_type=ActivityType.CREATED,
    )

    # 2. issue updated
    # TODO: I think we don't need this, but I might be wrong.

    # 3. assigned issue state changed
    raw_updated_issues = safe_traverse(response.data, "state_changed_issues.nodes", [])
    _process_batch_of_issues(
        raw_updated_issues, oldest_updated_at, activity_by_issue_id, activity_type=None
    )

    # 4. issue commented
    raw_comments: list[dict] = safe_traverse(
        response.data, "commented_issues.nodes", []
    )
    _process_comments(raw_comments, oldest_updated_at, activity_by_issue_id)

    #  5. comment reacted
    #
    # I can't get reactions at all. The problems are:
    # a) reactions don't have a root field, they are only accessible as a
    #    sub-field of either 1 specific comment or an issue or ...
    # b) I can't filter reactions by the author in GQL
    #
    # To get reactions, I could fetch ALL comments updated in the last 24h
    # by ALL people and get their reactions and then in Python filter
    # if the reaction-author is the current user.
    # Then I'd need to do the same for Issues, because a user can react to
    # the issue too.

    # 6. opened pull request
    # All PRs are fetched with every issue


def _process_batch_of_issues(
    raw_issues: list[dict],
    oldest_updated_at: datetime,
    activity_by_issue_id: dict[str, IssueActivity],
    activity_type: Literal[ActivityType.COMMENTED, ActivityType.CREATED] | None,
) -> None:
    for raw_issue in raw_issues:
        _process_one_issue(
            raw_issue,
            oldest_updated_at,
            activity_by_issue_id,
            activity_type=activity_type,
        )


def _process_comments(
    raw_comments: list[dict],
    oldest_updated_at: datetime,
    activity_by_issue_id: dict[str, IssueActivity],
) -> None:
    for raw_comment in raw_comments:
        raw_issue: dict | None = raw_comment.get("issue")
        if raw_issue is None:
            continue
        raw_issue[_COMMENTED_AT_KEY] = raw_comment["updatedAt"]  # faking the issue data
        _process_one_issue(
            raw_issue,
            oldest_updated_at,
            activity_by_issue_id,
            activity_type=ActivityType.COMMENTED,
        )


def _process_one_issue(
    raw_issue: dict,
    oldest_updated_at: datetime,
    activity_by_issue_id: dict[str, IssueActivity],
    *,
    activity_type: Literal[ActivityType.COMMENTED, ActivityType.CREATED] | None,
) -> None:
    issue_key = raw_issue["id"]

    # It's a bit hard to know what action actually took place. That is because of how we
    # fetch the data with GQL.

    activity: ActivityType
    activity_at: datetime
    match activity_type:
        case ActivityType.COMMENTED:
            activity = ActivityType.COMMENTED
            activity_at = parse_str_to_date(raw_issue[_COMMENTED_AT_KEY])
        case ActivityType.CREATED:
            activity = ActivityType.CREATED
            activity_at = parse_str_to_date(raw_issue["createdAt"])
        case _:
            activity, activity_at = _figure_out_activity(raw_issue, oldest_updated_at)

    title = raw_issue["title"]
    logger.debug(f"Adding issue {title=} {activity=} {activity_at=}")
    assert isinstance(activity_at, datetime)

    pr_attachments: list[str] = _extract_pr_attachments(raw_issue)

    activity_by_issue_id[issue_key] = IssueActivity(
        title=title,
        ident=raw_issue["identifier"],
        url=raw_issue["url"],
        activity_type=activity,
        state=LinearState.from_string(raw_issue["state"]["type"]),
        activity_at=activity_at,
        pr_attachments=pr_attachments,
    )


def _figure_out_activity(
    raw_issue: dict, oldest_updated_at: datetime
) -> tuple[ActivityType, datetime]:
    activities: dict[ActivityType, datetime] = {}

    key: str
    activity: ActivityType
    for key, activity in [
        ("completedAt", ActivityType.COMPLETED),
        ("canceledAt", ActivityType.CANCELED),
        ("startedAt", ActivityType.WORKED_ON),
    ]:
        if (
            dt := parse_optional_str_to_date(raw_issue.get(key))
        ) and dt >= oldest_updated_at:
            activities[activity] = dt

    if not activities:
        logger.error(
            f"Something went wrong, NO activity could be identified on the issue, "
            f"this must be a bug in the code. {raw_issue=}"
        )
        return ActivityType.UNKNOWN, datetime.now(tz=UTC)

    sorted_activities = sorted(activities.items(), key=lambda x: x[0], reverse=True)
    return sorted_activities[0]


def _extract_pr_attachments(raw_issue: dict) -> list[str]:
    raw_attachments: list[dict] = safe_traverse(raw_issue, "attachments.nodes", [])
    return [pr["url"] for pr in raw_attachments]


def _extract_page_info(
    one_page_response: GQLResponse,
) -> tuple[THasMorePages, TAfterCursor]:
    # TODO: should we support pagination? possibly ... but not now
    return False, ""
