from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from requests import Response

from standup_report.exceptions import RemoteException
from standup_report.remote.response_utils import check_status_code_of_response
from standup_report.remote.response_utils import extract_json_body

logger = logging.getLogger(__name__)


@dataclass
class GQLResponse:
    response: Response
    data: dict


@dataclass
class RESTResponse:
    response: Response
    data: dict


def post_gql_query(
    *,
    gql_url: str,
    headers: dict,
    query: str,
    variables: dict | None = None,
) -> GQLResponse:
    gql_name = (
        gql_url.replace("/graphql", "")
        .replace("https://", "")
        .replace("api.", "")
        .replace(".com", "")
    )
    logger.info(f"Calling {gql_name.upper()} GraphQL {variables=}")
    try:
        response: Response = requests.post(
            url=gql_url,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=30,
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise RemoteException(f"Request to `{gql_name}` raised an exception") from exc

    check_status_code_of_response(response)
    response_data, json_err = extract_json_body(response)

    if json_err:
        raise RemoteException(
            "Response is not a valid JSON", query=query, variables=variables
        ) from json_err

    if response_data is None:
        raise RemoteException("Response was None", query=query, variables=variables)

    gql_data: dict | None = response_data.get("data")
    gql_errors: list[dict] | None = response_data.get("errors")

    if gql_data is None:
        raise RemoteException(
            "Response did not contain any data.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    if gql_errors:
        raise RemoteException(
            "Errors in response.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    return GQLResponse(data=gql_data, response=response)


def get_rest_response(
    *,
    full_url: str,
    headers: dict,
    params: dict | None = None,
) -> RESTResponse:
    """Make a GET request to a REST API."""
    logger.info(f"GET {full_url} {params=}")
    try:
        response: Response = requests.get(
            url=full_url,
            headers=headers,
            params=params,
            timeout=30,
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise RemoteException(f"Request to `{full_url}` raised an exception") from exc

    check_status_code_of_response(response)
    response_data, json_err = extract_json_body(response)

    if json_err:
        raise RemoteException(
            "Response is not a valid JSON", url=full_url, query=str(params)
        ) from json_err

    if response_data is None:
        raise RemoteException("Response was None", url=full_url, query=str(params))

    return RESTResponse(data=response_data, response=response)
