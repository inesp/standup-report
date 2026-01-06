import logging
from collections.abc import Iterable

from standup_report.issue_type import Issue
from standup_report.issue_type import IssueAttachment
from standup_report.issue_type import LinearState
from standup_report.linear.pr_attach import extract_pr_attachments
from standup_report.remote.base_client import GQLResponse
from standup_report.remote.gql_utils import TAfterCursor
from standup_report.remote.gql_utils import THasMorePages
from standup_report.remote.gql_utils import extract_gql_query_from_file
from standup_report.settings import get_settings

from . import client

logger = logging.getLogger(__name__)


def fetch_in_progress_issues() -> Iterable[Issue]:
    logger.info("---------- Fetch in-progress issues")
    authored_prs_query: str = extract_gql_query_from_file(
        "standup_report/linear/open_issues.graphql"
    )

    has_more_pages: THasMorePages = True
    user_email = get_settings().LINEAR_EMAIL

    while has_more_pages:
        one_page_response = client.post_linear_gql_query(
            query=authored_prs_query,
            variables={"email": user_email},
        )
        yield from _process_one_page_of_issues(one_page_response)
        has_more_pages, _ = _extract_page_info(one_page_response)


def _process_one_page_of_issues(response: GQLResponse) -> Iterable[Issue]:
    raw_issues: list[dict] = response.data["open_issues"]["nodes"]

    for raw_issue in raw_issues:
        pr_attachments: list[IssueAttachment] = extract_pr_attachments(raw_issue)

        issue = Issue(
            title=raw_issue["title"],
            ident=raw_issue["identifier"],
            url=raw_issue["url"],
            state=LinearState.from_string(raw_issue["state"]["type"]),
            pr_attachments=pr_attachments,
        )
        logger.debug(f"Found {issue=}")
        yield issue


def _extract_page_info(
    one_page_response: GQLResponse,
) -> tuple[THasMorePages, TAfterCursor]:
    # I don't know... more than 100 issues? we can't even handle that in UI
    return False, None
