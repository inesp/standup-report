import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field

import duckdb

logger = logging.getLogger(__name__)

# Use a file-based DuckDB for persistence
DB_FILE_PATH = "standup_report.duckdb"


def get_connection_obj() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=DB_FILE_PATH)


@contextmanager
def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    conn = get_connection_obj()
    try:
        yield conn
    finally:
        conn.close()


# Table definitions
TABLE_SCHEMAS = {
    "ignored_items": """
        CREATE TABLE IF NOT EXISTS ignored_items (
            item_type VARCHAR NOT NULL,
            item_id VARCHAR NOT NULL,
            item_title VARCHAR NOT NULL,
            ignored_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (item_type, item_id)
        )
    """,
    "notes": """
        CREATE TABLE IF NOT EXISTS notes (
            item_type VARCHAR NOT NULL,
            item_id VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            note TEXT,
            PRIMARY KEY (item_type, item_id, category)
        )
    """,
}


def create_tables() -> None:
    """Create all required DuckDB tables."""
    with get_connection() as conn:

        for table_name, schema in TABLE_SCHEMAS.items():
            conn.execute(schema)
            logger.debug(f"Created/verified table: {table_name}")

        logger.info("All DuckDB tables created/verified")


def recreate_tables() -> None:
    """Drop the database file and recreate all tables."""

    # Close any existing connections by creating a temporary one and closing it
    with get_connection():
        pass

    if os.path.exists(DB_FILE_PATH):
        os.remove(DB_FILE_PATH)
        logger.debug(f"Deleted database file: {DB_FILE_PATH}")

    create_tables()


@dataclass
class HealthState:
    status: str
    tables: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    error_msg: str = field(default="")

    @property
    def database_file(self) -> str:
        return DB_FILE_PATH


def health_check() -> HealthState:
    """Check DuckDB connection and basic functionality."""
    with get_connection() as conn:
        try:
            # Test basic query
            result = conn.execute("SELECT 1 as test").fetchone()
            test_passed = result is not None and result[0] == 1

            create_tables()

            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()

            table_names: list[str] = [table[0] for table in tables]

            row_counts: dict[str, int] = {}
            for table_name in ["ignored_items", "notes"]:
                if table_name in table_names:
                    count_result = conn.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()
                    if count_result:
                        row_counts[table_name] = count_result[0]

            return HealthState(
                status="healthy" if test_passed else "error",
                tables=table_names,
                row_counts=row_counts,
            )

        except Exception as e:
            return HealthState(status="error", error_msg=str(e))
