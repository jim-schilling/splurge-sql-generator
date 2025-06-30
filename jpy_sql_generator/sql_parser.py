"""
SQL Parser for extracting method names and SQL queries from template files.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
import keyword  # Added for reserved keyword check
from pathlib import Path
from typing import Dict, Tuple, Any

from jpy_sql_generator.sql_helper import FETCH_STATEMENT, detect_statement_type


class SqlParser:
    """Parser for SQL files with method name comments."""

    # Only allow valid Python identifiers for method names
    _METHOD_PATTERN = re.compile(r"^\s*#\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*$", re.MULTILINE)
    # Only allow valid Python identifiers for parameter names
    _PARAM_PATTERN = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")

    # Query type constants (private)
    _TYPE_SELECT = "select"
    _TYPE_INSERT = "insert"
    _TYPE_UPDATE = "update"
    _TYPE_DELETE = "delete"
    _TYPE_CTE = "cte"
    _TYPE_VALUES = "values"
    _TYPE_SHOW = "show"
    _TYPE_EXPLAIN = "explain"
    _TYPE_DESCRIBE = "describe"
    _TYPE_OTHER = "other"

    # SQL keyword constants (private)
    _KW_SELECT = "SELECT"
    _KW_INSERT = "INSERT"
    _KW_UPDATE = "UPDATE"
    _KW_DELETE = "DELETE"
    _KW_WITH = "WITH"
    _KW_VALUES = "VALUES"
    _KW_SHOW = "SHOW"
    _KW_EXPLAIN = "EXPLAIN"
    _KW_DESC = "DESC"
    _KW_DESCRIBE = "DESCRIBE"
    _KW_RETURNING = "RETURNING"

    def __init__(self) -> None:
        pass  # No need to compile pattern in __init__

    def parse_file(self, file_path: str | Path) -> Tuple[str, Dict[str, str]]:
        """
        Parse a SQL file and extract class name and method-query mappings.

        Args:
            file_path: Path to the SQL file

        Returns:
            Tuple of (class_name, method_queries_dict)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            raise OSError(f"Error reading SQL file {file_path}: {e}") from e

        # Extract class name from first line comment
        lines = content.split("\n")
        if not lines or not lines[0].strip().startswith("#"):
            raise ValueError(
                f"First line must be a class comment starting with #: {file_path}"
            )

        class_comment = lines[0].strip()
        if not class_comment.startswith("# "):
            raise ValueError(f"Class comment must start with '# ': {class_comment}")

        class_name = class_comment[2:].strip()  # Remove '# ' prefix
        if not class_name:
            raise ValueError(f"Class name cannot be empty: {class_comment}")
        if not class_name.isidentifier() or keyword.iskeyword(class_name):
            raise ValueError(f"Class name must be a valid Python identifier and not a reserved keyword: {class_name}")

        # Parse methods and queries
        method_queries = self._extract_methods_and_queries(content)

        return class_name, method_queries

    def _extract_methods_and_queries(self, content: str) -> Dict[str, str]:
        """
        Extract method names and their corresponding SQL queries.

        Args:
            content: SQL file content

        Returns:
            Dictionary mapping method names to SQL queries
        """
        method_queries = {}

        # Split content by method comments
        parts = self._METHOD_PATTERN.split(content)

        # Skip the first part (content before first method)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                method_name = parts[i].strip()
                sql_query = parts[i + 1].strip()

                # Clean up the SQL query - remove trailing semicolon if present
                if sql_query.endswith(";"):
                    sql_query = sql_query[:-1]

                # Check for valid Python identifier and not a reserved keyword
                if method_name and sql_query:
                    if not method_name.isidentifier() or keyword.iskeyword(method_name):
                        raise ValueError(f"Method name must be a valid Python identifier and not a reserved keyword: {method_name}")
                    method_queries[method_name] = sql_query

        return method_queries

    def get_method_info(self, sql_query: str) -> Dict[str, Any]:
        """
        Analyze SQL query to determine method type and parameters.
        Uses sql_helper.detect_statement_type() for accurate statement type detection.

        Args:
            sql_query: SQL query string

        Returns:
            Dictionary with method analysis info
        """
        # Use sql_helper to determine if this is a fetch or execute statement
        statement_type = detect_statement_type(sql_query)
        is_fetch = statement_type == FETCH_STATEMENT

        # Determine query type based on first keyword
        sql_upper = sql_query.upper().strip()
        if sql_upper.startswith(self._KW_SELECT):
            query_type = self._TYPE_SELECT
        elif sql_upper.startswith(self._KW_INSERT):
            query_type = self._TYPE_INSERT
        elif sql_upper.startswith(self._KW_UPDATE):
            query_type = self._TYPE_UPDATE
        elif sql_upper.startswith(self._KW_DELETE):
            query_type = self._TYPE_DELETE
        elif sql_upper.startswith(self._KW_WITH):
            query_type = self._TYPE_CTE
        elif sql_upper.startswith(self._KW_VALUES):
            query_type = self._TYPE_VALUES
        elif sql_upper.startswith(self._KW_SHOW):
            query_type = self._TYPE_SHOW
        elif sql_upper.startswith(self._KW_EXPLAIN):
            query_type = self._TYPE_EXPLAIN
        elif sql_upper.startswith(self._KW_DESC) or sql_upper.startswith(self._KW_DESCRIBE):
            query_type = self._TYPE_DESCRIBE
        else:
            query_type = self._TYPE_OTHER

        # Extract parameters (named parameters like :param_name, valid Python identifiers only)
        parameters = self._PARAM_PATTERN.findall(sql_query)
        # Deduplicate while preserving order
        parameters = list(dict.fromkeys(parameters))
        # Check for reserved keywords in parameters
        for param in parameters:
            if keyword.iskeyword(param):
                raise ValueError(f"Parameter name cannot be a reserved keyword: {param}")

        return {
            "type": query_type,
            "is_fetch": is_fetch,
            "statement_type": statement_type,  # Add the detected statement type
            "parameters": parameters,
            "has_returning": self._KW_RETURNING in sql_upper,
        }
