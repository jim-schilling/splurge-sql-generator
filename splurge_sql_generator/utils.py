"""
Utility functions shared across the splurge_sql_generator package.

This module contains common helper functions used by multiple modules
to reduce code duplication and improve maintainability.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import keyword
import re
from pathlib import Path
from typing import Any

from .exceptions import (
    SplurgeSqlGeneratorFileNotFoundError,
    SplurgeSqlGeneratorSqlValidationError,
    SplurgeSqlGeneratorValueError,
)

DOMAINS = ["util"]


# Private constants for common operations
_SNAKE_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
_SQL_SIZE_PATTERN = re.compile(r"\(\s*\d+(?:\s*,\s*\d+)?\s*\)")

# Private constants for file extensions
_SQL_EXTENSION = ".sql"
_SCHEMA_EXTENSION = ".schema"
_YAML_EXTENSION = ".yaml"

# Private constants for encoding
_DEFAULT_ENCODING = "utf-8"


def to_snake_case(class_name: str) -> str:
    """
    Convert PascalCase class name to snake_case filename.

    Args:
        class_name: PascalCase class name (e.g., 'UserRepository')

    Returns:
        Snake case filename (e.g., 'user_repository')

    Examples:
        >>> to_snake_case('UserRepository')
        'user_repository'
        >>> to_snake_case('ProductService')
        'product_service'
        >>> to_snake_case('API')
        'api'
    """
    if not class_name:
        return class_name

    # Special-case all-uppercase acronyms (e.g., "API" -> "api")
    if class_name.isupper():
        return class_name.lower()

    # Insert underscore before capital letters, then convert to lowercase
    snake_case = _SNAKE_CASE_PATTERN.sub("_", class_name).lower()
    return snake_case


def clean_sql_type(sql_type: str) -> str:
    """
    Clean and normalize SQL type by removing size specifications.

    Args:
        sql_type: Raw SQL type string

    Returns:
        Cleaned SQL type string

    Examples:
        >>> clean_sql_type('VARCHAR(255)')
        'VARCHAR'
        >>> clean_sql_type('DECIMAL(10,2)')
        'DECIMAL'
        >>> clean_sql_type('INTEGER')
        'INTEGER'
    """
    if not sql_type:
        return sql_type

    # Remove size specifications like (255), (10,2)
    cleaned = _SQL_SIZE_PATTERN.sub("", sql_type).strip()
    return cleaned


def find_files_by_extension(directory: str | Path, extension: str) -> list[Path]:
    """
    Find all files with a specific extension in a directory.

    Args:
        directory: Directory to search in
        extension: File extension to search for (e.g., '.sql', '.schema')

    Returns:
        List of Path objects for matching files
    """
    path = Path(directory)
    if not path.exists():
        return []

    return list(path.glob(f"*{extension}"))


def validate_python_identifier(name: str, *, context: str = "identifier", file_path: str | Path | None = None) -> None:
    """
    Validate that a string is a valid Python identifier.

    Args:
        name: String to validate
        context: Context for error messages (e.g., "class name", "method name")
        file_path: Optional file path for error context

    Raises:
        SplurgeSqlGeneratorValueError: If name is not a valid Python identifier
    """
    if not name:
        file_context = f" in {file_path}" if file_path else ""
        raise SplurgeSqlGeneratorValueError(f"{context.capitalize()} cannot be empty{file_context}")

    if not name.isidentifier():
        file_context = f" in {file_path}" if file_path else ""
        raise SplurgeSqlGeneratorValueError(
            f"{context.capitalize()} must be a valid Python identifier{file_context}: {name}"
        )

    if keyword.iskeyword(name):
        file_context = f" in {file_path}" if file_path else ""
        raise SplurgeSqlGeneratorValueError(
            f"{context.capitalize()} cannot be a reserved keyword{file_context}: {name}"
        )


class InputValidator:
    """Centralized input validation with fail-fast approach."""

    @staticmethod
    def sql_file_path(path: str | Path, context: str = "SQL file") -> Path:
        """
        Validate SQL file path.

        Args:
            path: File path to validate
            context: Context description for error messages

        Returns:
            Validated Path object

        Raises:
            SplurgeSqlGeneratorValueError: If path is not a .sql file
            SplurgeSqlGeneratorFileNotFoundError: If file doesn't exist
        """
        p = Path(path)
        if p.suffix.lower() != ".sql":
            raise SplurgeSqlGeneratorValueError(f"{context} must have .sql extension, got: {path}")
        if not p.exists():
            raise SplurgeSqlGeneratorFileNotFoundError(f"{context} not found: {path}")
        return p

    @staticmethod
    def sql_content(content: str, context: str = "SQL content") -> str:
        """
        Validate SQL content is non-empty.

        Args:
            content: SQL content to validate
            context: Context description for error messages

        Returns:
            Stripped SQL content

        Raises:
            SplurgeSqlGeneratorSqlValidationError: If content is empty or whitespace-only
        """
        if not content or not content.strip():
            raise SplurgeSqlGeneratorSqlValidationError(f"{context} cannot be empty or whitespace-only")
        return content.strip()

    @staticmethod
    def identifier(name: str, context: str = "identifier") -> str:
        """
        Validate Python identifier.

        Args:
            name: Name to validate
            context: Context description for error messages (e.g., "class name", "method name")

        Returns:
            Validated identifier

        Raises:
            SplurgeSqlGeneratorValueError: If name is not a valid Python identifier
        """
        if not name:
            raise SplurgeSqlGeneratorValueError(f"{context.capitalize()} cannot be empty")

        if not name.isidentifier():
            raise SplurgeSqlGeneratorValueError(f"{context.capitalize()} must be valid Python identifier: {name}")

        if keyword.iskeyword(name):
            raise SplurgeSqlGeneratorValueError(f"{context.capitalize()} cannot be reserved keyword: {name}")

        return name


def format_error_context(file_path: str | Path | None = None) -> str:
    """
    Format file path for error context messages.

    Args:
        file_path: Optional file path

    Returns:
        Formatted error context string
    """
    if file_path is None:
        return ""
    return f" in {file_path}"


def normalize_string(value: Any) -> str:
    """
    Safely convert any value to a normalized string.

    Args:
        value: Value to convert

    Returns:
        Normalized string
    """
    if value is None:
        return ""
    return str(value).strip()


def is_empty_or_whitespace(value: Any) -> bool:
    """
    Check if a value is empty or contains only whitespace.

    Args:
        value: Value to check

    Returns:
        True if value is empty or whitespace-only
    """
    if value is None:
        return True
    return not str(value).strip()
