from flask import Blueprint
from flask import redirect
from flask import request
from flask import url_for
from werkzeug.wrappers import Response

from standup_report import google
from standup_report.settings import GoogleSettings
from standup_report.settings import get_settings

google_auth_bp = Blueprint("google_auth", __name__, url_prefix="/google")


@google_auth_bp.route("/auth")
def start_auth() -> Response | tuple[str, int]:
    """Start the OAuth flow by redirecting to Google."""
    google_settings: GoogleSettings = get_settings().GOOGLE

    if not google_settings.HAS_CREDENTIALS:
        return "Missing credentials.json file. See README for setup instructions.", 400

    redirect_uri = url_for("google_auth.oauth_callback", _external=True)
    flow = google.start_oauth_flow(redirect_uri)

    authorization_url, _ = flow.authorization_url(  # type: ignore[no-untyped-call]
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return redirect(authorization_url)


@google_auth_bp.route("/oauth/callback")
def oauth_callback() -> Response | tuple[str, int]:
    """Handle the OAuth callback from Google."""
    if "error" in request.args:
        error = request.args.get("error")
        return f"OAuth error: {error}", 400

    redirect_uri = url_for("google_auth.oauth_callback", _external=True)
    flow = google.start_oauth_flow(redirect_uri)

    flow.fetch_token(authorization_response=request.url)  # type: ignore[no-untyped-call]

    credentials = flow.credentials
    google.save_oauth_token(credentials)

    return redirect(url_for("home.index"))
