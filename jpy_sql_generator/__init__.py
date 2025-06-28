"""
jpy_sql_generator - Python code generator for SQLAlchemy classes from SQL templates.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.

This package provides tools to generate Python classes with SQLAlchemy methods
from SQL template files, with sophisticated SQL parsing and statement type detection.
"""

from jpy_sql_generator.sql_helper import (
    detect_statement_type,
    FETCH_STATEMENT,
    EXECUTE_STATEMENT,
    remove_sql_comments,
    parse_sql_statements,
    split_sql_file
)
from jpy_sql_generator.sql_parser import SqlParser
from jpy_sql_generator.code_generator import PythonCodeGenerator

__version__ = "0.1.2"
__author__ = "Jim Schilling"

__all__ = [
    # SQL Helper functions
    'detect_statement_type',
    'FETCH_STATEMENT', 
    'EXECUTE_STATEMENT',
    'remove_sql_comments',
    'parse_sql_statements',
    'split_sql_file',
    
    # Core classes
    'SqlParser',
    'PythonCodeGenerator',
]


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


def generate_class(sql_file_path: str, output_file_path: str = None) -> str:
    """
    Convenience function to generate a Python class from a SQL file.
    
    Args:
        sql_file_path: Path to the SQL template file
        output_file_path: Optional path to save the generated Python file
        
    Returns:
        Generated Python code as string
    """
    generator = PythonCodeGenerator()
    return generator.generate_class(sql_file_path, output_file_path)


def generate_multiple_classes(sql_files: list, output_dir: str = None) -> dict:
    """
    Convenience function to generate multiple Python classes from SQL files.
    
    Args:
        sql_files: List of SQL file paths
        output_dir: Optional directory to save generated files
        
    Returns:
        Dictionary mapping class names to generated code
    """
    generator = PythonCodeGenerator()
    return generator.generate_multiple_classes(sql_files, output_dir)
