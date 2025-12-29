from __future__ import annotations

import logging
from dataclasses import dataclass
from http import HTTPMethod
from urllib.parse import urlencode

import requests
from requests import Response

from standup_report.exceptions import GitHubException
from standup_report.github.response_utils import check_status_code_of_response
from standup_report.github.response_utils import extract_json_body
from standup_report.settings import get_settings

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.github.com/graphql"
_REST_URL = "https://api.github.com"


@dataclass
class GHResponse:
    response: Response
    data: dict


def post_gql_query(query: str, variables: dict | None = None) -> GHResponse:
    logger.info(f"Calling Github GraphQL {variables=}")
    token = get_settings().GH_TOKEN
    try:
        response: Response = requests.post(
            url=_GQL_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Accept": "application/vnd.github.moondragon+json",
                "Authorization": f"Bearer {token}",
            },
            timeout=30,
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise GitHubException("Request to GitHub raised an exception") from exc

    check_status_code_of_response(response)
    response_data, json_err = extract_json_body(response)

    if json_err:
        raise GitHubException(
            "Response is not a valid JSON", query=query, variables=variables
        ) from json_err

    if response_data is None:
        raise GitHubException("Response was None", query=query, variables=variables)

    gql_data: dict | None = response_data.get("data")
    gql_errors: list[dict] | None = response_data.get("errors")

    if gql_data is None:
        raise GitHubException(
            "Response did not contain any data.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    if gql_errors:
        raise GitHubException(
            "Errors in response.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    return GHResponse(data=gql_data, response=response)


def _build_full_url(url_path: str, query_parameters: dict | None) -> str:
    query_str: str = f"?{urlencode(query_parameters)}" if query_parameters else ""

    if url_path.startswith("/"):
        return f"{_REST_URL}{url_path}{query_str}"

    if url_path.startswith(_REST_URL):
        return f"{url_path}{query_str}"

    raise GitHubException(
        f"An invalid url path was requested url:{url_path} rest_url:{_REST_URL}",
    )


def make_rest_request(
    url_path: str,
    method: HTTPMethod = HTTPMethod.GET,
    *,
    query_params: dict | None = None,
    json: dict | None = None,
):
    token = get_settings().GH_TOKEN
    full_url: str = _build_full_url(url_path, query_params)
    logger.info(f"Calling Github REST {full_url=}")

    try:
        response: Response = requests.request(
            method=method,
            url=full_url,
            json=json,
            headers={
                "Accept": "application/vnd.github.moondragon+json",
                "Authorization": f"Bearer {token}",
            },
            timeout=30,
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise GitHubException(
            "Request to GitHub raised an exception", url=full_url
        ) from exc

    check_status_code_of_response(response)
    response_data, json_err = extract_json_body(response)

    if json_err:
        raise GitHubException(
            "Response is not a valid JSON", url=full_url
        ) from json_err

    if response_data is None:
        raise GitHubException("Response was None", url=full_url)

    # errors: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#client-errors
    if isinstance(response_data, dict):
        message = response_data.get("message")
        raise GitHubException(f"Response error: `{message}`", url=full_url)

    return GHResponse(data=response_data, response=response)
