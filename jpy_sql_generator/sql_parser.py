"""
SQL Parser for extracting method names and SQL queries from template files.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
from pathlib import Path
from typing import Dict, Tuple
from jpy_sql_generator.sql_helper import detect_statement_type, FETCH_STATEMENT


class SqlParser:
    """Parser for SQL files with method name comments."""
    
    def __init__(self):
        self.method_pattern = re.compile(r'^#\s*(\w+)\s*$', re.MULTILINE)
    
    def parse_file(self, file_path: str | Path) -> Tuple[str, Dict[str, str]]:
        """
        Parse a SQL file and extract class name and method-query mappings.
        
        Args:
            file_path: Path to the SQL file
            
        Returns:
            Tuple of (class_name, method_queries_dict)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except OSError as e:
            raise OSError(f"Error reading SQL file {file_path}: {e}") from e
        
        # Extract class name from first line comment
        lines = content.split('\n')
        if not lines or not lines[0].strip().startswith('#'):
            raise ValueError(f"First line must be a class comment starting with #: {file_path}")
        
        class_comment = lines[0].strip()
        if not class_comment.startswith('# '):
            raise ValueError(f"Class comment must start with '# ': {class_comment}")
        
        class_name = class_comment[2:].strip()  # Remove '# ' prefix
        if not class_name:
            raise ValueError(f"Class name cannot be empty: {class_comment}")
        
        # Parse methods and queries
        method_queries = self._extract_methods_and_queries(content)
        
        return class_name, method_queries
    
    def _extract_methods_and_queries(self, content: str) -> Dict[str, str]:
        """
        Extract method names and their corresponding SQL queries.
        
        Args:
            content: SQL file content
            
        Returns:
            Dictionary mapping method names to SQL queries
        """
        method_queries = {}
        
        # Split content by method comments
        parts = self.method_pattern.split(content)
        
        # Skip the first part (content before first method)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                method_name = parts[i].strip()
                sql_query = parts[i + 1].strip()
                
                # Clean up the SQL query - remove trailing semicolon if present
                if sql_query.endswith(';'):
                    sql_query = sql_query[:-1]
                
                if method_name and sql_query:
                    method_queries[method_name] = sql_query
        
        return method_queries
    
    def get_method_info(self, sql_query: str) -> Dict[str, any]:
        """
        Analyze SQL query to determine method type and parameters.
        Uses sql_helper.detect_statement_type() for accurate statement type detection.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Dictionary with method analysis info
        """
        # Use sql_helper to determine if this is a fetch or execute statement
        statement_type = detect_statement_type(sql_query)
        is_fetch = statement_type == FETCH_STATEMENT
        
        # Determine query type based on first keyword
        sql_upper = sql_query.upper().strip()
        if sql_upper.startswith('SELECT'):
            query_type = 'select'
        elif sql_upper.startswith('INSERT'):
            query_type = 'insert'
        elif sql_upper.startswith('UPDATE'):
            query_type = 'update'
        elif sql_upper.startswith('DELETE'):
            query_type = 'delete'
        elif sql_upper.startswith('WITH'):
            query_type = 'cte'
        elif sql_upper.startswith('VALUES'):
            query_type = 'values'
        elif sql_upper.startswith('SHOW'):
            query_type = 'show'
        elif sql_upper.startswith('EXPLAIN'):
            query_type = 'explain'
        elif sql_upper.startswith('DESC') or sql_upper.startswith('DESCRIBE'):
            query_type = 'describe'
        else:
            query_type = 'other'
        
        # Extract parameters (named parameters like :param_name)
        param_pattern = re.compile(r':(\w+)')
        parameters = param_pattern.findall(sql_query)
        # Deduplicate while preserving order
        parameters = list(dict.fromkeys(parameters))
        
        return {
            'type': query_type,
            'is_fetch': is_fetch,
            'statement_type': statement_type,  # Add the detected statement type
            'parameters': parameters,
            'has_returning': 'RETURNING' in sql_upper
        } 