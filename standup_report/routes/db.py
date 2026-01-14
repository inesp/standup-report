import logging

from flask import Blueprint
from flask import redirect
from werkzeug import Response

from standup_report import duckdb_client

logger = logging.getLogger(__name__)

db = Blueprint("db", __name__)


@db.route("/recreate_db")
def recreate_db() -> Response:
    """Reset all DuckDB tables (drop and recreate)."""
    logger.info("Resetting DuckDB tables")
    duckdb_client.recreate_tables()
    # redirect home
    return redirect("/")
