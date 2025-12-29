# Public API for DuckDB client
from .client import health_check as duckdb_health_check
from .client import recreate_tables

__all__ = [
    "duckdb_health_check",
    "recreate_tables",
]
