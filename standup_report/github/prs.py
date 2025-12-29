import logging
from datetime import datetime

from standup_report.date_utils import parse_str_to_date
from standup_report.dict_utils import safe_traverse
from standup_report.github import client
from standup_report.github.client import GHResponse
from standup_report.github.gql_utils import extract_gql_query_from_file
from standup_report.github.gql_utils import parse_page_info
from standup_report.pr_type import OwnPR
from standup_report.pr_type import PRState
from standup_report.settings import get_settings

logger = logging.getLogger(__name__)


THasMorePages = bool
TAfterCursor = str | None


def fetch_authored_prs(oldest_updated_at: datetime):
    logger.info("---------- Fetching PRs I've worked on in the last 24h")
    authored_prs_query: str = extract_gql_query_from_file(
        "standup_report/github/prs.graphql"
    )

    # Queries longer than 256 characters are not supported
    # You can't construct a query using more than five AND, OR, or NOT operators
    # https://docs.github.com/en/search-github/getting-started-with-searching-on-github/troubleshooting-search-queries

    # maye also: mentions:USERNAME??

    # reviews:
    # 	is:pr commenter:@me matches pull requests you have commented on.

    has_more_pages: THasMorePages = True
    after_cursor: TAfterCursor = None

    user_login_name = get_settings().GH_USERNAME

    oldest_updated_at_str: str = oldest_updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    search_query: str = (
        f"author:{user_login_name} is:pr updated:>{oldest_updated_at_str} sort:updated"
    )

    while has_more_pages:
        one_page_response = client.post_gql_query(
            query=authored_prs_query,
            variables={"searchQuery": search_query},
        )
        yield from _process_one_page_of_prs(one_page_response, user_login_name)
        has_more_pages, after_cursor = _extract_page_info(one_page_response)


def _process_one_page_of_prs(response: GHResponse, user_login_name: str):
    raw_prs: list[dict] = response.data["search"]["nodes"]

    for pr_data in raw_prs:
        raw_state = pr_data["state"]
        pr = OwnPR(
            number=pr_data["number"],
            repo_slug=pr_data["repository"]["nameWithOwner"],
            title=pr_data["title"],
            url=pr_data["url"],
            author=user_login_name,
            created_at=parse_str_to_date(pr_data["createdAt"]),
            merged_at=(
                parse_str_to_date(pr_data["mergedAt"]) if pr_data["mergedAt"] else None
            ),
            state=PRState[raw_state] if raw_state in PRState else None,
            last_change=parse_str_to_date(pr_data["updatedAt"]),
        )
        logger.info(f"Found PR(number={pr.number}), url={pr.url}, {pr.title=}")
        yield pr


def _extract_page_info(
    one_page_response: GHResponse,
) -> tuple[THasMorePages, TAfterCursor]:
    pr_data: dict | None = safe_traverse(one_page_response.data, "search")
    return parse_page_info(pr_data)
