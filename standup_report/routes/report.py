import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import render_template

from standup_report import github
from standup_report.pr_type import OwnPR
from standup_report.settings import get_settings

report_bp = Blueprint("report", __name__)
logger = logging.getLogger(__name__)

@report_bp.route("/report")
def build_report():
    about_24h_ago = datetime.now(UTC) - timedelta(hours=24 + 2)

    my_prs: list[OwnPR] = list(github.fetch_authored_prs(about_24h_ago))

    return render_template(
        "report.html",
        title="Standup Report",
        subtitle=f"What I did in the last 24h (since: {about_24h_ago})",
        my_prs=my_prs,
        since=about_24h_ago,
        settings=get_settings(),
    )
