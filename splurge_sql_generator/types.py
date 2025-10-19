"""
Type definitions for splurge_sql_generator.

This module provides type-safe data structures for representing SQL parsing results
and code generation metadata.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

from typing import TypedDict

DOMAINS = ["types"]


class ColumnInfo(TypedDict, total=False):
    """Type-safe definition of column information."""

    name: str
    """Column name"""

    sql_type: str
    """Original SQL type (e.g., VARCHAR(255))"""

    python_type: str
    """Mapped Python type annotation (e.g., str)"""

    nullable: bool
    """Whether column allows NULL values"""


class MethodInfo(TypedDict, total=False):
    """Type-safe definition of SQL method information."""

    name: str
    """Method name extracted from SQL comment"""

    sql_type: str
    """SQL statement type (SELECT, INSERT, UPDATE, DELETE, etc.)"""

    python_type: str
    """Inferred Python return type (e.g., list[Row], int)"""

    parameters: list[str]
    """List of extracted parameter names"""

    is_fetch: bool
    """True if statement returns rows (SELECT)"""

    statement_type: str
    """Statement classification: 'fetch' or 'execute'"""

    has_returning: bool
    """True if statement has RETURNING clause"""


class TableDefinition(TypedDict, total=False):
    """Type-safe definition of table information."""

    table_name: str
    """Table name"""

    columns: dict[str, ColumnInfo]
    """Column definitions mapped by column name"""

    schema: str | None
    """Optional schema/database name"""
