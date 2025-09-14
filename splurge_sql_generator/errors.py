"""
Custom exceptions for the splurge_sql_generator package.

These exceptions provide clear error signaling for file I/O and validation
concerns encountered while working with SQL inputs.
"""

from __future__ import annotations


class SqlFileError(Exception):
    """Raised when an error occurs while accessing or reading a SQL file."""


class SqlValidationError(ValueError):
    """Raised when provided SQL-related input arguments are invalid."""
