"""
Custom exceptions for the splurge_sql_generator package.

These exceptions provide clear error signaling for file I/O and validation
concerns encountered while working with SQL inputs.
"""

from __future__ import annotations

DOMAINS = ["exceptions"]


class SplurgeSqlGeneratorError(Exception):
    """Base exception for all errors in the splurge_sql_generator package."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details
        self.message = message


class FileError(SplurgeSqlGeneratorError):
    """Raised when an error occurs while accessing or reading a file."""


class SqlValidationError(SplurgeSqlGeneratorError):
    """Raised when provided SQL-related input arguments are invalid."""
