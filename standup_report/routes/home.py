from flask import Blueprint
from flask import render_template

from standup_report import github
from standup_report import linear
from standup_report.duckdb_client import duckdb_health_check
from standup_report.exceptions import RemoteException
from standup_report.exceptions import SettingsError
from standup_report.exceptions import StandupReportError
from standup_report.settings import Settings
from standup_report.settings import get_settings

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index() -> str:
    duckdb_health = None

    settings, settings_error = _get_settings_handle_err()

    if settings:
        duckdb_health = duckdb_health_check()

    gh_query, gh_response, gh_exc = _check_github_conn()
    linear_query, linear_response, linear_exc = _check_linear_conn()

    return render_template(
        "home.html",
        title="Configuration Check",
        subtitle="Checks your configuration and access to all system components",
        settings=settings,
        settings_error=settings_error,
        gh_response=gh_response,
        gh_exc=gh_exc if gh_exc else None,
        gh_query=gh_query,
        linear_query=linear_query,
        linear_response=linear_response,
        linear_exc=linear_exc,
        duckdb_health=duckdb_health,
    )


def _get_settings_handle_err() -> tuple[Settings, None] | tuple[None, str]:
    try:
        settings = get_settings()
        return settings, None
    except SettingsError as e:
        settings_error = str(e)
        return None, settings_error


def _check_github_conn() -> tuple[str, dict | None, StandupReportError | None]:
    gh_query = "{ viewer { login } }"
    gh_response: dict | None = None
    gh_exc: None | StandupReportError = None

    try:
        gh_response = github.client.post_github_gql_query(gh_query).data
    except (RemoteException, SettingsError) as exc:
        gh_exc = exc

    return gh_query, gh_response, gh_exc


def _check_linear_conn() -> tuple[str, dict | None, StandupReportError | None]:
    linear_query = "{ viewer { email } }"
    linear_response: dict | None = None
    linear_exc: None | StandupReportError = None

    try:
        linear_response = linear.client.post_linear_gql_query(linear_query).data
    except (RemoteException, SettingsError) as exc:
        linear_exc = exc

    return linear_query, linear_response, linear_exc
