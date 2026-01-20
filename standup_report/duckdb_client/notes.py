import logging

from standup_report.ignore_mixin import ItemType
from standup_report.note_utils import NoteCategory

from .client import get_connection

logger = logging.getLogger(__name__)


def add_note(
    item_type: ItemType, item_id: str, category: NoteCategory, note: str
) -> None:
    clean_note = note.strip()
    if not clean_note:
        remove_note(item_type, item_id, category)
        return
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO notes (item_type, item_id, category, note)
            VALUES (?, ?, ?, ?)
            """,
            [item_type, item_id, category, clean_note],
        )
        logger.info(f"Added {category} note for {item_type}: {item_id}")


def remove_note(item_type: ItemType, item_id: str, category: NoteCategory) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM notes WHERE item_type = ? AND item_id = ? AND category = ?",
            [item_type, item_id, category],
        )
        logger.info(f"Removed {category} note for {item_type}: {item_id}")


def get_notes() -> dict[tuple[ItemType, str, NoteCategory], str]:
    with get_connection() as conn:
        result = conn.execute(
            "SELECT item_type, item_id, category, note FROM notes"
        ).fetchall()
        return {
            (ItemType(row[0]), row[1], NoteCategory(row[2])): row[3] for row in result
        }


def delete_all_notes() -> int:
    with get_connection() as conn:
        result = conn.execute("SELECT COUNT(*) FROM notes").fetchone()
        count = result[0] if result else 0
        conn.execute("TRUNCATE notes")
        logger.info(f"Deleted all notes ({count} total)")
        return count
