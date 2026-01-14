import logging

from standup_report.ignore_mixin import ItemType

from .client import get_connection

logger = logging.getLogger(__name__)


def add_ignored_item(item_type: ItemType, item_id: str, item_title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO ignored_items (item_type, item_id, item_title, ignored_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [item_type, item_id, item_title],
        )
        logger.info(f"Ignored {item_type}: {item_id} {item_title}")


def remove_ignored_item(item_type: ItemType, item_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM ignored_items WHERE item_type = ? AND item_id = ?",
            [item_type, item_id],
        )
        logger.info(f"Unignored {item_type}: {item_id}")


def get_ignored_items() -> set[tuple[ItemType, str, str]]:
    with get_connection() as conn:
        result = conn.execute(
            "SELECT item_type, item_id, item_title FROM ignored_items ORDER BY ignored_at DESC"
        ).fetchall()
        return {(ItemType(row[0]), row[1], row[2]) for row in result}
