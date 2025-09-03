"""
Utility functions shared across the splurge_sql_generator package.

This module contains common helper functions used by multiple modules
to reduce code duplication and improve maintainability.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
from pathlib import Path
from typing import Any


# Private constants for common operations
_SNAKE_CASE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')
_SQL_SIZE_PATTERN = re.compile(r'\(\s*\d+(?:\s*,\s*\d+)?\s*\)')

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
    snake_case = _SNAKE_CASE_PATTERN.sub('_', class_name).lower()
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
    cleaned = _SQL_SIZE_PATTERN.sub('', sql_type).strip()
    return cleaned


def validate_file_path(file_path: str | Path, *, 
                      must_exist: bool = True,
                      extension: str | None = None) -> Path:
    """
    Validate and normalize a file path.
    
    Args:
        file_path: File path to validate
        must_exist: Whether the file must exist (default: True)
        extension: Expected file extension (e.g., '.sql', '.schema')
        
    Returns:
        Normalized Path object
        
    Raises:
        FileNotFoundError: If must_exist is True and file doesn't exist
        ValueError: If extension doesn't match expected extension
    """
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if extension and path.suffix.lower() != extension.lower():
        raise ValueError(f"File must have {extension} extension: {path}")
    
    return path


def safe_read_file(file_path: str | Path, *, encoding: str = _DEFAULT_ENCODING) -> str:
    """
    Safely read a file with proper error handling.
    
    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read due to permissions
        UnicodeDecodeError: If file contains invalid encoding
        OSError: For other I/O errors
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        return path.read_text(encoding=encoding)
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file '{path}': {e}") from e
    except UnicodeDecodeError as e:
        # Re-raise with proper UnicodeDecodeError signature while preserving context
        raise UnicodeDecodeError(
            encoding,
            e.object,
            e.start,
            e.end,
            f"Invalid {encoding} encoding in file '{path}': {e}"
        ) from e
    except OSError as e:
        raise OSError(f"Error reading file '{path}': {e}") from e


def safe_write_file(file_path: str | Path, content: str, *, 
                   encoding: str = _DEFAULT_ENCODING,
                   create_parents: bool = True) -> None:
    """
    Safely write content to a file with proper error handling.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        encoding: File encoding (default: utf-8)
        create_parents: Whether to create parent directories (default: True)
        
    Raises:
        PermissionError: If file cannot be written due to permissions
        OSError: For other I/O errors
    """
    path = Path(file_path)
    
    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(content, encoding=encoding)
    except PermissionError as e:
        raise PermissionError(f"Permission denied writing file '{path}': {e}") from e
    except OSError as e:
        raise OSError(f"Error writing file '{path}': {e}") from e


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


def validate_python_identifier(name: str, *, 
                             context: str = "identifier",
                             file_path: str | Path | None = None) -> None:
    """
    Validate that a string is a valid Python identifier.
    
    Args:
        name: String to validate
        context: Context for error messages (e.g., "class name", "method name")
        file_path: Optional file path for error context
        
    Raises:
        ValueError: If name is not a valid Python identifier
    """
    import keyword
    
    if not name:
        file_context = f" in {file_path}" if file_path else ""
        raise ValueError(f"{context.capitalize()} cannot be empty{file_context}")
    
    if not name.isidentifier():
        file_context = f" in {file_path}" if file_path else ""
        raise ValueError(f"{context.capitalize()} must be a valid Python identifier{file_context}: {name}")
    
    if keyword.iskeyword(name):
        file_context = f" in {file_path}" if file_path else ""
        raise ValueError(f"{context.capitalize()} cannot be a reserved keyword{file_context}: {name}")


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
