# Public API for DuckDB client
from .client import health_check as duckdb_health_check
from .client import recreate_tables
from .ignoring import add_ignored_item
from .ignoring import get_ignored_items
from .ignoring import remove_ignored_item
from .notes import add_note
from .notes import get_notes
from .notes import remove_note

__all__ = [
    "add_ignored_item",
    "add_note",
    "duckdb_health_check",
    "get_ignored_items",
    "get_notes",
    "recreate_tables",
    "remove_ignored_item",
    "remove_note",
]
