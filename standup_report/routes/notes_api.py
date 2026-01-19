import logging

from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import request

from standup_report import duckdb_client
from standup_report.ignore_mixin import ItemType
from standup_report.note_utils import NoteCategory

notes_api = Blueprint("notes_api", __name__)
logger = logging.getLogger(__name__)


@notes_api.route("/api/note/<item_type>/<path:item_id>/<category>", methods=["POST"])
def handle_note(
    item_type: str, item_id: str, category: str
) -> Response | tuple[Response, int]:
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
    del item_type

    clean_category = NoteCategory.from_string(category)
    if clean_category is None:
        return (
            jsonify(
                {
                    "error": f"invalid category, must be one of `{NoteCategory.DONE}`, `{NoteCategory.NEXT}`"
                }
            ),
            400,
        )
    del category

    data = request.get_json()
    if data is None:
        return jsonify({"error": "missing JSON body"}), 400

    note = data.get("note", "")

    if not note:
        duckdb_client.remove_note(clean_item_type, item_id, clean_category)

    duckdb_client.add_note(clean_item_type, item_id, clean_category, note)

    return jsonify(
        {
            "success": True,
            "item_type": clean_item_type,
            "item_id": item_id,
            "category": clean_category,
        }
    )
