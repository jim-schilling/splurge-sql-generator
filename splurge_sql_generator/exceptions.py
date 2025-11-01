"""
Custom exceptions for the splurge_sql_generator package.

These exceptions provide clear error signaling for file I/O and validation
concerns encountered while working with SQL inputs.
"""

from __future__ import annotations

import warnings

from ._vendor.splurge_exceptions.core.exceptions import SplurgeFrameworkError

DOMAINS = ["exceptions"]


def splurge_class_deprecated(reason=None, version=None):  # type: ignore
    """Decorator to mark a class as deprecated."""

    def decorator(cls):  # type: ignore
        # Issue a deprecation warning when the class is defined
        message = f"{cls.__name__} is deprecated"
        if version:
            message += f" since version {version}"
        if reason:
            message += f": {reason}"
        warnings.warn(message, category=DeprecationWarning, stacklevel=2)
        # Return the original class unchanged
        return cls

    return decorator


class SplurgeSqlGeneratorError(SplurgeFrameworkError):
    """Base exception for all errors in the splurge_sql_generator package."""

    _domain = "splurge-sql-generator"


class SplurgeSqlGeneratorValueError(SplurgeSqlGeneratorError):
    """Raised when a value-related error occurs."""

    _domain = "splurge-sql-generator.value"


class SplurgeSqlGeneratorTypeError(SplurgeSqlGeneratorError):
    """Raised when a type-related error occurs."""

    _domain = "splurge-sql-generator.type"


class SplurgeSqlGeneratorRuntimeError(SplurgeSqlGeneratorError):
    """Raised when a runtime error occurs."""

    _domain = "splurge-sql-generator.runtime"


class SplurgeSqlGeneratorOSError(SplurgeSqlGeneratorError):
    """Raised when an OS-related error occurs."""

    _domain = "splurge-sql-generator.os"


class SplurgeSqlGeneratorFileError(SplurgeSqlGeneratorError):
    """Raised when an error occurs while accessing or reading a file."""

    _domain = "splurge-sql-generator.file"


class SplurgeSqlGeneratorFileNotFoundError(SplurgeSqlGeneratorFileError):
    """Raised when a file is not found."""

    _domain = "splurge-sql-generator.file-not-found"


class SplurgeSqlGeneratorSqlValidationError(SplurgeSqlGeneratorError):
    """Raised when provided SQL-related input arguments are invalid."""

    _domain = "splurge-sql-generator.sql-validation"


# Parsing-specific exceptions
class SplurgeSqlGeneratorParsingError(SplurgeSqlGeneratorError):
    """Base exception for parsing-related errors."""

    _domain = "splurge-sql-generator.parsing"


class SplurgeSqlGeneratorSqlParsingError(SplurgeSqlGeneratorParsingError):
    """Raised when SQL parsing via sqlparse fails."""


class SplurgeSqlGeneratorTokenizationError(SplurgeSqlGeneratorParsingError):
    """Raised when token processing or traversal fails."""

    _domain = "splurge-sql-generator.tokenization"


# Schema-specific exceptions
class SplurgeSqlGeneratorSchemaError(SplurgeSqlGeneratorError):
    """Base exception for schema processing errors."""

    _domain = "splurge-sql-generator.schema"


class SplurgeSqlGeneratorColumnDefinitionError(SplurgeSqlGeneratorSchemaError):
    """Raised when column definition parsing fails."""

    _domain = "splurge-sql-generator.column-definition"


class SplurgeSqlGeneratorTypeInferenceError(SplurgeSqlGeneratorSchemaError):
    """Raised when type inference fails."""

    _domain = "splurge-sql-generator.type-inference"


# Configuration exceptions
class SplurgeSqlGeneratorConfigurationError(SplurgeSqlGeneratorError):
    """Raised when configuration is invalid or missing."""

    _domain = "splurge-sql-generator.configuration"


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the following exceptions are deprecated and will be removed in v2025.7.0.


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorFileError", version="2025.6.0")
class FileError(SplurgeSqlGeneratorError):
    """Raised when an error occurs while accessing or reading a file.

    Deprecated: Use SplurgeSqlGeneratorFileError instead."""

    _domain = "splurge-sql-generator.file"


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorSqlValidationError", version="2025.6.0")
class SqlValidationError(SplurgeSqlGeneratorError):
    """Raised when provided SQL-related input arguments are invalid."""

    _domain = "splurge-sql-generator.sql-validation"


# Parsing-specific exceptions


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorParsingError", version="2025.6.0")
class ParsingError(SplurgeSqlGeneratorError):
    """Base exception for parsing-related errors."""

    _domain = "splurge-sql-generator.parsing"


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorSqlParsingError", version="2025.6.0")
class SqlParsingError(ParsingError):
    """Raised when SQL parsing via sqlparse fails."""

    _domain = "splurge-sql-generator.parsing"


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorTokenizationError", version="2025.6.0")
class TokenizationError(ParsingError):
    """Raised when token processing or traversal fails."""

    _domain = "splurge-sql-generator.tokenization"


# Schema-specific exceptions


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorSchemaError", version="2025.6.0")
class SchemaError(SplurgeSqlGeneratorError):
    """Base exception for schema processing errors."""

    _domain = "splurge-sql-generator.schema"


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorColumnDefinitionError", version="2025.6.0")
class ColumnDefinitionError(SchemaError):
    """Raised when column definition parsing fails."""

    _domain = "splurge-sql-generator.column-definition"


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorTypeInferenceError", version="2025.6.0")
class TypeInferenceError(SchemaError):
    """Raised when type inference fails."""

    _domain = "splurge-sql-generator.type-inference"


# Configuration exceptions


@splurge_class_deprecated(reason="Use SplurgeSqlGeneratorConfigurationError", version="2025.6.0")
class ConfigurationError(SplurgeSqlGeneratorError):
    """Raised when configuration is invalid or missing."""

    _domain = "splurge-sql-generator.configuration"
