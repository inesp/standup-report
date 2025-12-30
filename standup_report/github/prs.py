import logging
from collections.abc import Iterable
from datetime import datetime

from standup_report.date_utils import parse_str_to_date
from standup_report.dict_utils import safe_traverse
from standup_report.github import client
from standup_report.pr_type import OwnPR
from standup_report.pr_type import PRReviewDecision
from standup_report.pr_type import PRState
from standup_report.remote.base_client import GQLResponse
from standup_report.remote.gql_utils import extract_gql_query_from_file
from standup_report.remote.gql_utils import parse_page_info
from standup_report.settings import get_settings

logger = logging.getLogger(__name__)


THasMorePages = bool
TAfterCursor = str | None


def fetch_authored_prs(oldest_updated_at: datetime) -> Iterable[OwnPR]:
    user_login_name = get_settings().GH_USERNAME

    oldest_updated_at_str: str = oldest_updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    search_query: str = (
        f"author:{user_login_name} is:pr updated:>{oldest_updated_at_str} sort:updated"
    )
    yield from _fetch_prs_by_query(search_query)


def fetch_authored_open_prs() -> Iterable[OwnPR]:
    user_login_name = get_settings().GH_USERNAME

    search_query: str = f"author:{user_login_name} is:pr state:open sort:updated"
    yield from _fetch_prs_by_query(search_query)


def _fetch_prs_by_query(search_query: str) -> Iterable[OwnPR]:
    logger.info("---------- Fetching PRs I've worked on in the last 24h")
    authored_prs_query: str = extract_gql_query_from_file(
        "standup_report/github/prs.graphql"
    )

    # Queries longer than 256 characters are not supported
    # You can't construct a query using more than five AND, OR, or NOT operators
    # https://docs.github.com/en/search-github/getting-started-with-searching-on-github/troubleshooting-search-queries

    has_more_pages: THasMorePages = True
    ignored_repos = get_settings().IGNORED_REPOS

    while has_more_pages:
        one_page_response = client.post_github_gql_query(
            query=authored_prs_query,
            variables={"searchQuery": search_query},
        )
        yield from _process_one_page_of_prs(one_page_response, ignored_repos)
        has_more_pages, _ = _extract_page_info(one_page_response)


def _process_one_page_of_prs(
    response: GQLResponse, ignored_repos: set[str]
) -> Iterable[OwnPR]:
    raw_prs: list[dict] = response.data["search"]["nodes"]

    for pr_data in raw_prs:
        number: int = pr_data["number"]
        repo_slug: str = pr_data["repository"]["nameWithOwner"]
        if repo_slug in ignored_repos:
            logger.info(f"Ignoring PR #{number} in {repo_slug}")
            continue

        raw_state = pr_data["state"]
        state: PRState = PRState.from_string(raw_state)  # type: ignore[assignment]
        raw_review_decision = pr_data["reviewDecision"]
        pr = OwnPR(
            number=number,
            repo_slug=repo_slug,
            title=pr_data["title"],
            url=pr_data["url"],
            created_at=parse_str_to_date(pr_data["createdAt"]),
            merged_at=(
                parse_str_to_date(pr_data["mergedAt"]) if pr_data["mergedAt"] else None
            ),
            state=state,
            last_change=parse_str_to_date(pr_data["updatedAt"]),
            review_decision=PRReviewDecision.from_string(raw_review_decision),
        )
        logger.info(
            f"Found PR(number={pr.number}), {pr.title=} {repo_slug=} {pr_data["reviewDecision"]}"
        )
        yield pr


def _extract_page_info(
    one_page_response: GQLResponse,
) -> tuple[THasMorePages, TAfterCursor]:
    pr_data: dict | None = safe_traverse(one_page_response.data, "search")
    return parse_page_info(pr_data)
