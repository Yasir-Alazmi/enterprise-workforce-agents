import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core.config import settings
from src.core.logging import get_logger
from src.tools.base import BaseTool, ToolResult

logger = get_logger(__name__)

FORBIDDEN_SQL_PATTERNS = [
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r";",  # Prevent stacked multi-statement injection
    r"--", # Comments
]


class SafeSQLTool(BaseTool):
    """Sandboxed read-only SQL query execution tool with AST/regex safety enforcement."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = Path(db_path or settings.db_path)
        if not self._db_path.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).resolve().parent.parent.parent
            self._db_path = project_root / self._db_path
        self._forbidden_regex = re.compile("|".join(FORBIDDEN_SQL_PATTERNS), re.IGNORECASE)

    @property
    def name(self) -> str:
        return "safe_sql_query"

    @property
    def description(self) -> str:
        return (
            "Executes sandboxed read-only SELECT queries on the enterprise database. "
            "Available tables: departments, employees, procurement_orders, audit_logs."
        )

    def validate_query(self, query: str) -> Tuple[bool, str]:
        cleaned = query.strip()
        if not cleaned.lower().startswith("select"):
            return False, "Security Violation: Only SELECT queries are permitted."

        match = self._forbidden_regex.search(cleaned)
        if match:
            forbidden_token = match.group(0)
            return False, f"Security Violation: Forbidden SQL statement/token detected: '{forbidden_token}'."

        return True, ""

    def get_schema(self) -> Dict[str, List[str]]:
        """Return database schema for agent introspection."""
        if not self._db_path.exists():
            return {}

        conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]

        schema: Dict[str, List[str]] = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            cols = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
            schema[table] = cols

        conn.close()
        return schema

    def execute(self, query: str, max_rows: Optional[int] = None) -> ToolResult:
        is_valid, err_msg = self.validate_query(query)
        if not is_valid:
            logger.warning("Blocked unsafe SQL query: %s | Reason: %s", query, err_msg)
            return ToolResult(success=False, error=err_msg, metadata={"query": query})

        limit = max_rows or settings.max_query_rows
        t0 = time.perf_counter()

        try:
            # Open connection strictly in read-only mode using URI
            conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True, timeout=settings.query_timeout_seconds)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchmany(limit)
            result_dicts = [dict(row) for row in rows]
            duration_ms = (time.perf_counter() - t0) * 1000.0
            conn.close()

            return ToolResult(
                success=True,
                data=result_dicts,
                metadata={
                    "row_count": len(result_dicts),
                    "execution_ms": round(duration_ms, 2),
                    "query": query
                }
            )
        except Exception as e:
            logger.error("SQL Execution failed: %s", e)
            return ToolResult(success=False, error=str(e), metadata={"query": query})
