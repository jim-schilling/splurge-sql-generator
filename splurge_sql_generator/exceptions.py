"""
Custom exceptions for the splurge_sql_generator package.

These exceptions provide clear error signaling for file I/O and validation
concerns encountered while working with SQL inputs.
"""

from __future__ import annotations

from ._vendor.splurge_exceptions.core.exceptions import SplurgeFrameworkError

DOMAINS = ["exceptions"]


class SplurgeSqlGeneratorError(SplurgeFrameworkError):
    """Base exception for all errors in the splurge_sql_generator package."""

    _domain = "splurge-sql-generator"


class FileError(SplurgeSqlGeneratorError):
    """Raised when an error occurs while accessing or reading a file."""

    _domain = "splurge-sql-generator.file"


class SqlValidationError(SplurgeSqlGeneratorError):
    """Raised when provided SQL-related input arguments are invalid."""

    _domain = "splurge-sql-generator.sql-validation"


# Parsing-specific exceptions
class ParsingError(SplurgeSqlGeneratorError):
    """Base exception for parsing-related errors."""

    _domain = "splurge-sql-generator.parsing"


class SqlParsingError(ParsingError):
    """Raised when SQL parsing via sqlparse fails."""


class TokenizationError(ParsingError):
    """Raised when token processing or traversal fails."""

    _domain = "splurge-sql-generator.tokenization"


# Schema-specific exceptions
class SchemaError(SplurgeSqlGeneratorError):
    """Base exception for schema processing errors."""

    _domain = "splurge-sql-generator.schema"


class ColumnDefinitionError(SchemaError):
    """Raised when column definition parsing fails."""

    _domain = "splurge-sql-generator.column-definition"


class TypeInferenceError(SchemaError):
    """Raised when type inference fails."""

    _domain = "splurge-sql-generator.type-inference"


# Configuration exceptions
class ConfigurationError(SplurgeSqlGeneratorError):
    """Raised when configuration is invalid or missing."""

    _domain = "splurge-sql-generator.configuration"
