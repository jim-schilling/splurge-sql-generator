"""
SQL Parser for extracting method names and SQL queries from template files.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
from pathlib import Path
from typing import Any

import splurge_safe_io.exceptions as safe_io_exc
import sqlparse
from splurge_safe_io.safe_text_file_reader import SafeTextFileReader
from sqlparse import tokens as T

from splurge_sql_generator.exceptions import FileError, SqlValidationError
from splurge_sql_generator.sql_helper import (
    FETCH_STATEMENT,
    detect_statement_type,
    extract_table_names,
    remove_sql_comments,
)
from splurge_sql_generator.utils import (
    format_error_context,
    validate_python_identifier,
)

DOMAINS = ["parser", "sql"]


class SqlParser:
    """Parser for SQL files with method name comments."""

    # Only allow valid Python identifiers for method names
    _METHOD_PATTERN = re.compile(r"^\s*#\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*$", re.MULTILINE)
    # Only allow valid Python identifiers for parameter names
    _PARAM_PATTERN = re.compile(r"(?<!:):([a-zA-Z_][a-zA-Z0-9_]*)\b")

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
        """
        Initialize the SQL parser.

        No initialization required as patterns are compiled at module level.
        """
        pass  # No need to compile pattern in __init__

    def parse_file(self, file_path: str | Path) -> tuple[str, dict[str, str]]:
        """
        Parse a SQL file and extract class name and method-query mappings.

        Args:
            file_path: Path to the SQL file

        Returns:
            Tuple of (class_name, method_queries_dict)

        Raises:
            FileNotFoundError: If the SQL file does not exist
            OSError: If there are I/O errors reading the file
            SqlValidationError: If the file format is invalid
        """
        try:
            reader = SafeTextFileReader(file_path)
            content = reader.read()
            return self.parse_string(content, file_path)
        except safe_io_exc.SplurgeSafeIoPathValidationError as e:
            raise FileError(message=f"SQL file path is invalid: {str(file_path)}.", details=str(e.message)) from e
        except safe_io_exc.SplurgeSafeIoFileNotFoundError as e:
            raise FileError(message=f"SQL file not found: '{str(file_path)}'.", details=str(e.message)) from e
        except safe_io_exc.SplurgeSafeIoFilePermissionError as e:
            raise FileError(
                message=f"Permission denied reading SQL file: {str(file_path)}.", details=str(e.message)
            ) from e
        except safe_io_exc.SplurgeSafeIoFileDecodingError as e:
            raise FileError(
                message=f"Decoding error reading SQL file: {str(file_path)}.", details=str(e.message)
            ) from e
        except safe_io_exc.SplurgeSafeIoOsError as e:
            raise FileError(message=f"OS error reading SQL file: {str(file_path)}.", details=str(e.message)) from e
        except safe_io_exc.SplurgeSafeIoUnknownError as e:
            raise FileError(message=f"Unknown error reading SQL file: {str(file_path)}.", details=str(e.message)) from e

    def parse_string(self, content: str, file_path: str | Path | None = None) -> tuple[str, dict[str, str]]:
        """
        Parse SQL content string and extract class name and method-query mappings.

        Args:
            content: SQL file content as string
            file_path: Optional file path for error messages (default: None)

        Returns:
            Tuple of (class_name, method_queries_dict)

        Raises:
            SqlValidationError: If the content format is invalid
        """
        # Extract class name from first line comment
        lines = content.split("\n")
        if not lines or not lines[0].strip().startswith("#"):
            file_context = format_error_context(file_path)
            raise SqlValidationError(f"First line must be a class comment starting with #{file_context}")

        # Check if first line starts with "#" (before stripping)
        if not lines[0].startswith("#"):
            file_context = format_error_context(file_path)
            raise SqlValidationError(f"First line must be a class comment starting with #{file_context}")

        class_comment = lines[0].strip()
        class_name = class_comment[1:].strip()  # Remove '#' prefix

        # Validate class name using utility function
        try:
            validate_python_identifier(class_name, context="class name", file_path=file_path)
        except ValueError as e:
            raise SqlValidationError(str(e)) from e

        # Parse methods and queries
        method_queries = self._extract_methods_and_queries(content, file_path)

        return class_name, method_queries

    def _extract_methods_and_queries(self, content: str, file_path: str | Path | None = None) -> dict[str, str]:
        """
        Extract method names and their corresponding SQL queries.

        Args:
            content: SQL file content
            file_path: Optional file path for error messages (default: None)

        Returns:
            Dictionary mapping method names to SQL queries

        Raises:
            SqlValidationError: If method names are invalid
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
                    try:
                        validate_python_identifier(method_name, context="method name", file_path=file_path)
                        method_queries[method_name] = sql_query
                    except ValueError as e:
                        raise SqlValidationError(str(e)) from e

        return method_queries

    def get_method_info(self, sql_query: str, file_path: str | Path | None = None) -> dict[str, Any]:
        """
        Analyze SQL query to determine method type and parameters.
        Uses sql_helper.detect_statement_type() for accurate statement type detection.

        Args:
            sql_query: SQL query string
            file_path: Optional file path for error messages (default: None)

        Returns:
            Dictionary with method analysis info

        Raises:
            SqlValidationError: If parameter names are invalid
        """
        # Guard clause: trivial inputs return default analysis without extra work
        if not sql_query or not sql_query.strip():
            return {
                "type": self._TYPE_OTHER,
                "is_fetch": False,
                "statement_type": detect_statement_type(sql_query),
                "parameters": [],
                "has_returning": False,
            }

        # Use sql_helper to determine if this is a fetch or execute statement
        # This leverages the sophisticated sqlparse-based analysis in sql_helper
        statement_type = detect_statement_type(sql_query)
        is_fetch = statement_type == FETCH_STATEMENT

        # Determine query type based on statement type and SQL content
        # Remove comments first for more accurate analysis
        clean_sql = remove_sql_comments(sql_query)
        sql_upper = clean_sql.upper().strip()

        # Use statement_type to determine query type more accurately
        if statement_type == FETCH_STATEMENT:
            if sql_upper.startswith(self._KW_SELECT):
                query_type = self._TYPE_SELECT
            elif sql_upper.startswith(self._KW_VALUES):
                query_type = self._TYPE_VALUES
            elif sql_upper.startswith(self._KW_SHOW):
                query_type = self._TYPE_SHOW
            elif sql_upper.startswith(self._KW_EXPLAIN):
                query_type = self._TYPE_EXPLAIN
            elif sql_upper.startswith(self._KW_DESC) or sql_upper.startswith(self._KW_DESCRIBE):
                query_type = self._TYPE_DESCRIBE
            elif sql_upper.startswith(self._KW_WITH):
                query_type = self._TYPE_CTE
            else:
                query_type = self._TYPE_OTHER
        else:
            # Execute statements
            if sql_upper.startswith(self._KW_INSERT):
                query_type = self._TYPE_INSERT
            elif sql_upper.startswith(self._KW_UPDATE):
                query_type = self._TYPE_UPDATE
            elif sql_upper.startswith(self._KW_DELETE):
                query_type = self._TYPE_DELETE
            elif sql_upper.startswith(self._KW_WITH):
                query_type = self._TYPE_CTE
            else:
                query_type = self._TYPE_OTHER

        # Extract parameters (named parameters like :param_name) ignoring comments and string literals
        # 1) Remove comments
        param_scan_sql = remove_sql_comments(sql_query)
        parameters: list[str] = []
        seen: set[str] = set()
        try:
            parsed_params = sqlparse.parse(param_scan_sql)
            if parsed_params:
                tokens = list(parsed_params[0].flatten())

                def next_non_ws(idx: int) -> tuple[int | None, Any]:
                    j = idx + 1
                    while j < len(tokens):
                        t = tokens[j]
                        # Skip whitespace and comments tokens
                        if t.is_whitespace or t.ttype in T.Comment:
                            j += 1
                            continue
                        return j, t
                    return None, None

                for i, tok in enumerate(tokens):
                    val = str(tok.value)
                    # Skip anything inside string literals
                    if tok.ttype in T.Literal.String:
                        continue
                    # Direct placeholder like ":param"
                    if tok.ttype in (T.Name.Placeholder,):
                        name = val[1:] if val.startswith(":") else val
                        if name and name not in seen:
                            seen.add(name)
                            parameters.append(name)
                        continue
                    # Some dialects tokenize ":" and identifier separately
                    if tok.ttype is T.Punctuation and val == ":":
                        nxt_idx, nxt_tok = next_non_ws(i)
                        if nxt_tok and nxt_tok.ttype in (T.Name, T.Name.Placeholder):
                            name = str(nxt_tok.value)
                            # Ensure it matches identifier pattern
                            if self._PARAM_PATTERN.fullmatch(":" + name):
                                if name not in seen:
                                    seen.add(name)
                                    parameters.append(name)
        except Exception:
            # Fallback to regex on comment-stripped SQL if sqlparse fails
            parameters = list(dict.fromkeys(self._PARAM_PATTERN.findall(param_scan_sql)))
        # Check for reserved keywords in parameters
        for param in parameters:
            try:
                validate_python_identifier(param, context="parameter name", file_path=file_path)
            except ValueError as e:
                raise SqlValidationError(str(e)) from e

        return {
            "type": query_type,
            "is_fetch": is_fetch,
            "statement_type": statement_type,
            "parameters": parameters,
            "has_returning": self._KW_RETURNING in sql_upper,
        }

    def get_table_names(self, sql_query: str) -> list[str]:
        """
        Extract table names from SQL query using sql_helper.

        Args:
            sql_query: SQL query string

        Returns:
            List of table names referenced in the query
        """
        return extract_table_names(sql_query)
