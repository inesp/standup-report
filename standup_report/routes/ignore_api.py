import logging

from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import request

from standup_report import duckdb_client
from standup_report.enum_utils import SafeStrEnum
from standup_report.ignore_mixin import ItemType

ignore_api = Blueprint("ignore_api", __name__)
logger = logging.getLogger(__name__)


class IgnoreAction(SafeStrEnum):
    IGNORE = "ignore"
    UNIGNORE = "unignore"


@ignore_api.route("/api/<action>/<item_type>/<path:item_id>", methods=["GET"])
def handle_ignore(
    action: str, item_type: str, item_id: str
) -> Response | tuple[Response, int]:
    item_title: str | None = request.args.get("title")
    clean_action = IgnoreAction.from_string(action)
    if clean_action is None:
        return (
            jsonify(
                {
                    "error": f"invalid action, must be one of `{IgnoreAction.IGNORE}`, `{IgnoreAction.UNIGNORE}`"
                }
            ),
            400,
        )

    clean_item_type = ItemType.from_string(item_type)
    if clean_item_type is None:
        return (
            jsonify(
                {
                    "error": f"invalid item_type, must be one of `{ItemType.PR}`, `{ItemType.ISSUE}`"
                }
            ),
            400,
        )

    if clean_action == IgnoreAction.IGNORE:
        if not item_title:
            return jsonify({"error": "missing required param: item_title"}), 400
        duckdb_client.add_ignored_item(clean_item_type, item_id, item_title)
    else:
        duckdb_client.remove_ignored_item(clean_item_type, item_id)

    return jsonify(
        {
            "success": True,
            "item_type": item_type,
            "item_id": item_id,
            "item_title": item_title,
        }
    )
