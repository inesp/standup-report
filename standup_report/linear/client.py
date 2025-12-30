from __future__ import annotations

import logging

from standup_report.remote.base_client import GQLResponse
from standup_report.remote.base_client import post_gql_query
from standup_report.settings import get_settings

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.linear.app/graphql"


def post_linear_gql_query(query: str, variables: dict | None = None) -> GQLResponse:
    token = get_settings().LINEAR_TOKEN
    return post_gql_query(
        gql_url=_GQL_URL,
        headers={"Authorization": str(token)},
        query=query,
        variables=variables,
    )
