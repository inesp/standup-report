from flask import Blueprint
from flask import render_template

from standup_report.duckdb_client import duckdb_health_check
from standup_report.exceptions import GitHubException
from standup_report.exceptions import SettingsError
from standup_report.github import github_client
from standup_report.settings import Settings
from standup_report.settings import get_settings

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    gh_query = "{ viewer { login } }"
    gh_response = None
    gh_exc: None | GitHubException = None
    duckdb_health = None

    settings, settings_error = _get_settings_handle_err()

    print(settings)
    if settings:
        duckdb_health = duckdb_health_check()

        try:
            gh_response = github_client.post_gql_query(gh_query)
        except GitHubException as exc:
            gh_exc = exc

    return render_template(
        "home.html",
        title="Configuration Check",
        subtitle="Checks your configuration and access to all system components",
        settings=settings,
        settings_error=settings_error,
        gh_response=gh_response.data if gh_response else None,
        gh_exc=gh_exc if gh_exc else None,
        gh_query=gh_query,
        duckdb_health=duckdb_health,
    )


def _get_settings_handle_err() -> tuple[Settings, None] | tuple[None, str]:
    try:
        settings = get_settings()
        return settings, None
    except SettingsError as e:
        settings_error = str(e)
        return None, settings_error
