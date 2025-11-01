"""
splurge_sql_generator - Python code generator for SQLAlchemy classes from SQL templates.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.

This package provides tools to generate Python classes with SQLAlchemy methods
from SQL template files, with sophisticated SQL parsing and statement type detection.
"""

from .code_generator import PythonCodeGenerator
from .schema_parser import SchemaParser
from .sql_helper import (
    EXECUTE_STATEMENT,
    FETCH_STATEMENT,
    detect_statement_type,
    parse_sql_statements,
    remove_sql_comments,
    split_sql_file,
)
from .sql_parser import SqlParser

__version__ = "2025.6.0"

__all__ = [
    # SQL Helper functions
    "detect_statement_type",
    "remove_sql_comments",
    "parse_sql_statements",
    "split_sql_file",
    # Core classes
    "SqlParser",
    "PythonCodeGenerator",
    "SchemaParser",
    # Convenience functions
    "generate_class",
    "generate_multiple_classes",
    "generate_types_file",
    # Statement helpers (kept public for convenience)
    "is_fetch_statement",
    "is_execute_statement",
]

__domains__ = ["cli", "code", "exceptions", "generator", "misc", "parser", "schema", "sql", "util"]


def is_fetch_statement(sql: str) -> bool:
    """
    Convenience function to check if a SQL statement returns rows.

    Args:
        sql: SQL statement string

    Returns:
        True if statement returns rows (fetch), False otherwise (execute)

    Examples:
        >>> is_fetch_statement("SELECT * FROM users")
        True
        >>> is_fetch_statement("INSERT INTO users VALUES (1, 'John')")
        False
        >>> is_fetch_statement("WITH cte AS (SELECT 1) SELECT * FROM cte")
        True
    """
    return detect_statement_type(sql) == FETCH_STATEMENT


def is_execute_statement(sql: str) -> bool:
    """
    Convenience function to check if a SQL statement performs operations without returning rows.

    Args:
        sql: SQL statement string

    Returns:
        True if statement performs operations (execute), False otherwise (fetch)

    Examples:
        >>> is_execute_statement("INSERT INTO users VALUES (1, 'John')")
        True
        >>> is_execute_statement("SELECT * FROM users")
        False
        >>> is_execute_statement("UPDATE users SET active = 1")
        True
    """
    return detect_statement_type(sql) == EXECUTE_STATEMENT


def generate_class(
    sql_file_path: str,
    *,
    output_file_path: str | None = None,
    schema_file_path: str,
) -> str:
    """
    Convenience function to generate a Python class from a SQL file.

    Args:
        sql_file_path: Path to the SQL template file
        output_file_path: Optional path to save the generated Python file
        schema_file_path: Path to the schema file (required)

    Returns:
        Generated Python code as string
    """
    generator = PythonCodeGenerator()
    return generator.generate_class(
        sql_file_path,
        output_file_path=output_file_path,
        schema_file_path=schema_file_path,
    )


def generate_multiple_classes(
    sql_files: list[str],
    *,
    output_dir: str | None = None,
    schema_file_path: str,
) -> dict[str, str]:
    """
    Convenience function to generate multiple Python classes from SQL files.

    Args:
        sql_files: List of SQL file paths
        output_dir: Optional directory to save generated files
        schema_file_path: Path to a shared schema file (required)

    Returns:
        Dictionary mapping class names to generated code
    """
    generator = PythonCodeGenerator()
    return generator.generate_multiple_classes(sql_files, output_dir=output_dir, schema_file_path=schema_file_path)


def generate_types_file(*, output_path: str | None = None) -> str:
    """
    Convenience function to generate the default SQL type mapping YAML file.

    Args:
        output_path: Optional path to save the types file. If None, saves as 'types.yaml' in current directory.

    Returns:
        Path to the generated types file

    Examples:
        >>> generate_types_file()
        'types.yaml'
        >>> generate_types_file('custom_types.yaml')
        'custom_types.yaml'
    """
    schema_parser = SchemaParser()
    return schema_parser.generate_types_file(output_path=output_path)
