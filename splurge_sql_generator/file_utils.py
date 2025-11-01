"""
File I/O utilities and abstractions for splurge_sql_generator.

This module provides testable abstractions for file operations and configuration
reading to reduce coupling and improve testability.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from ._vendor.splurge_safe_io.exceptions import (
    SplurgeSafeIoFileNotFoundError,
    SplurgeSafeIoLookupError,
    SplurgeSafeIoOSError,
    SplurgeSafeIoPathValidationError,
    SplurgeSafeIoPermissionError,
    SplurgeSafeIoRuntimeError,
    SplurgeSafeIoUnicodeError,
)
from ._vendor.splurge_safe_io.safe_text_file_reader import SafeTextFileReader
from ._vendor.splurge_safe_io.safe_text_file_writer import open_safe_text_writer
from .exceptions import SplurgeSqlGeneratorConfigurationError, SplurgeSqlGeneratorFileError

DOMAINS = ["file", "utilities"]


class FileIoAdapter(ABC):
    """Abstract interface for file I/O operations."""

    @abstractmethod
    def read_text(self, path: str | Path, *, encoding: str = "utf-8") -> str:
        """
        Read file as text.

        Args:
            path: File path to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            SplurgeSqlGeneratorFileError: If file cannot be read
        """

    @abstractmethod
    def write_text(self, path: str | Path, content: str, *, encoding: str = "utf-8") -> None:
        """
        Write text to file.

        Args:
            path: File path to write to
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            SplurgeSqlGeneratorFileError: If file cannot be written
        """

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """


class SafeTextFileIoAdapter(FileIoAdapter):
    """Adapter wrapping SafeTextFileReader/Writer with error translation."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._logger = logging.getLogger(__name__)

    def read_text(self, path: str | Path, *, encoding: str = "utf-8") -> str:
        """
        Read file as text using SafeTextFileReader.

        Args:
            path: File path to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            SplurgeSqlGeneratorFileError: If file cannot be read
        """
        try:
            reader = SafeTextFileReader(path, encoding=encoding)
            content = reader.read()
            if not isinstance(content, str):
                raise SplurgeSqlGeneratorFileError(f"Unexpected return type from SafeTextFileReader: {type(content)}")
            return content
        except SplurgeSafeIoPathValidationError as e:
            raise SplurgeSqlGeneratorFileError(f"Invalid file path: {path}", details={"details": str(e.message)}) from e
        except SplurgeSafeIoFileNotFoundError as e:
            raise SplurgeSqlGeneratorFileError(f"File not found: {path}", details={"details": str(e.message)}) from e
        except SplurgeSafeIoPermissionError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Permission denied reading {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoLookupError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Lookup error reading {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoUnicodeError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Encoding error reading {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoOSError as e:
            raise SplurgeSqlGeneratorFileError(f"OS error reading {path}", details={"details": str(e.message)}) from e
        except SplurgeSafeIoRuntimeError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Runtime error reading {path}", details={"details": str(e.message)}
            ) from e

    def write_text(self, path: str | Path, content: str, *, encoding: str = "utf-8") -> None:
        """
        Write text to file using SafeTextFileWriter.

        Args:
            path: File path to write to
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            SplurgeSqlGeneratorFileError: If file cannot be written
        """
        try:
            with open_safe_text_writer(path, encoding=encoding) as writer:
                writer.write(content)
        except SplurgeSafeIoPathValidationError as e:
            raise SplurgeSqlGeneratorFileError(f"Invalid file path: {path}", details={"details": str(e.message)}) from e
        except SplurgeSafeIoUnicodeError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Encoding error writing to {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoPermissionError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Permission denied writing to {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoOSError as e:
            raise SplurgeSqlGeneratorFileError(
                f"OS error writing to {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoLookupError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Lookup error writing to {path}", details={"details": str(e.message)}
            ) from e
        except SplurgeSafeIoRuntimeError as e:
            raise SplurgeSqlGeneratorFileError(
                f"Runtime error writing to {path}", details={"details": str(e.message)}
            ) from e

    def exists(self, path: str | Path) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        return Path(path).exists()


class YamlConfigReader:
    """Read and parse YAML configuration files."""

    def __init__(self, file_io: FileIoAdapter | None = None) -> None:
        """
        Initialize the YAML config reader.

        Args:
            file_io: Optional FileIoAdapter. If None, uses SafeTextFileIoAdapter.
        """
        self._file_io = file_io or SafeTextFileIoAdapter()
        self._logger = logging.getLogger(__name__)

    def read(self, path: str | Path) -> dict[str, Any]:
        """
        Read and parse YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML content as dictionary

        Raises:
            SplurgeSqlGeneratorFileError: If file cannot be read
            SplurgeSqlGeneratorConfigurationError: If YAML is invalid or not a dictionary
        """
        try:
            content = self._file_io.read_text(path)
            parsed = yaml.safe_load(content)

            if not isinstance(parsed, dict):
                self._logger.warning(
                    f"YAML file {path} must contain a dictionary, got {type(parsed).__name__}. "
                    "Returning empty dictionary."
                )
                return {}

            self._logger.debug(f"Successfully loaded {len(parsed)} entries from YAML file: {path}")
            return parsed

        except SplurgeSqlGeneratorFileError:
            # Re-raise file errors as-is
            raise
        except yaml.YAMLError as e:
            raise SplurgeSqlGeneratorConfigurationError(
                f"Invalid YAML syntax in {path}", details={"details": str(e)}
            ) from e
        except Exception as e:
            raise SplurgeSqlGeneratorConfigurationError(
                f"Error reading YAML from {path}", details={"details": str(e)}
            ) from e
