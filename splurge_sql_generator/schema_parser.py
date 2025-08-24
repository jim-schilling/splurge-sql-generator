"""
Schema parser for SQL table definitions.

This module parses SQL schema files to extract column type information
for accurate Python type inference in generated code.

Copyright (c) 2025 Jim Schilling

This module is licensed under the MIT License.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class SchemaParser:
    """Parser for SQL schema files to extract column type information."""

    def __init__(self, *, sql_type_mapping_file: str = "types.yaml") -> None:
        """
        Initialize the schema parser.
        
        Args:
            sql_type_mapping_file: Path to the SQL type mapping YAML file
        """
        self._logger = logging.getLogger(__name__)
        self._sql_type_mapping = self._load_sql_type_mapping(sql_type_mapping_file)
        self._table_schemas: Dict[str, Dict[str, str]] = {}

    @property
    def table_schemas(self) -> Dict[str, Dict[str, str]]:
        """Public read-only access to the table schemas."""
        return self._table_schemas

    def _load_sql_type_mapping(self, mapping_file: str) -> Dict[str, str]:
        """
        Load SQL type to Python type mapping from YAML file.
        
        Args:
            mapping_file: Path to the mapping file
            
        Returns:
            Dictionary mapping SQL types to Python types
        """
        try:
            mapping_path = Path(mapping_file)
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # Return default mapping if file doesn't exist
                return self._get_default_mapping()
        except (OSError, IOError, ValueError, yaml.YAMLError) as e:
            self._logger.warning(f"Failed to load SQL type mapping file '{mapping_file}': {e}")
            # Fallback to default mapping on any error
            return self._get_default_mapping()

    def _get_default_mapping(self) -> Dict[str, str]:
        """
        Get default SQL type to Python type mapping.
        
        Returns:
            Default mapping dictionary
        """
        return {
            # SQLite types
            'INTEGER': 'int',
            'INT': 'int',
            'BIGINT': 'int',
            'TEXT': 'str',
            'VARCHAR': 'str',
            'CHAR': 'str',
            'DECIMAL': 'float',
            'REAL': 'float',
            'FLOAT': 'float',
            'DOUBLE': 'float',
            'BOOLEAN': 'bool',
            'BOOL': 'bool',
            'TIMESTAMP': 'str',
            'DATETIME': 'str',
            'DATE': 'str',
            'BLOB': 'bytes',
            
            # PostgreSQL types
            'JSON': 'dict',
            'JSONB': 'dict',
            'UUID': 'str',
            'SERIAL': 'int',
            'BIGSERIAL': 'int',
            
            # MySQL types
            'TINYINT': 'int',
            'SMALLINT': 'int',
            'MEDIUMINT': 'int',
            'LONGTEXT': 'str',
            'ENUM': 'str',
            
            # MSSQL types
            'BIT': 'bool',
            'NUMERIC': 'float',
            'MONEY': 'float',
            'SMALLMONEY': 'float',
            'NCHAR': 'str',
            'NVARCHAR': 'str',
            'NTEXT': 'str',
            'BINARY': 'bytes',
            'VARBINARY': 'bytes',
            'IMAGE': 'bytes',
            'DATETIME2': 'str',
            'SMALLDATETIME': 'str',
            'TIME': 'str',
            'DATETIMEOFFSET': 'str',
            'ROWVERSION': 'str',
            'UNIQUEIDENTIFIER': 'str',
            'XML': 'str',
            'SQL_VARIANT': 'Any',
            
            # Oracle types
            'NUMBER': 'float',
            'VARCHAR2': 'str',
            'NVARCHAR2': 'str',
            'CLOB': 'str',
            'NCLOB': 'str',
            'LONG': 'str',
            'RAW': 'bytes',
            'ROWID': 'str',
            'INTERVAL': 'str',
            
            'DEFAULT': 'Any'
        }

    def parse_schema_file(self, schema_file_path: str) -> Dict[str, Dict[str, str]]:
        """
        Parse a SQL schema file and extract column type information.
        
        Args:
            schema_file_path: Path to the schema file
            
        Returns:
            Dictionary mapping table names to column type mappings
        """
        try:
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            return self._parse_schema_content(schema_content)
        except FileNotFoundError:
            return {}
        except (OSError, IOError, ValueError, yaml.YAMLError) as e:
            self._logger.warning(f"Failed to parse schema file '{schema_file_path}': {e}")
            # Return empty dict on parsing errors
            return {}

    def _parse_schema_content(self, content: str) -> Dict[str, Dict[str, str]]:
        """
        Parse schema content and extract table column information.
        
        Args:
            content: SQL schema content
            
        Returns:
            Dictionary mapping table names to column type mappings
        """
        tables: Dict[str, Dict[str, str]] = {}
        
        # Remove comments and normalize whitespace
        content = self._remove_sql_comments(content)
        
        # Find all CREATE TABLE statements
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\);'
        matches = re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            table_name = match.group(1)
            table_body = match.group(2)
            
            # Parse column definitions
            columns = self._parse_table_columns(table_body)
            tables[table_name] = columns
        
        return tables

    def _remove_sql_comments(self, content: str) -> str:
        """
        Remove SQL comments from content.
        
        Args:
            content: SQL content with comments
            
        Returns:
            Content with comments removed
        """
        # Remove single-line comments (--)
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        
        # Remove multi-line comments (/* */)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        return content

    def _parse_table_columns(self, table_body: str) -> Dict[str, str]:
        """
        Parse column definitions from table body.
        
        Args:
            table_body: Table body content between parentheses
            
        Returns:
            Dictionary mapping column names to SQL types
        """
        columns: Dict[str, str] = {}
        
        # Split by commas, but be careful about commas in constraints
        # This is a simplified approach - for complex schemas, a proper SQL parser would be better
        lines = [line.strip() for line in table_body.split('\n')]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('PRIMARY KEY') or line.startswith('FOREIGN KEY') or line.startswith('UNIQUE') or line.startswith('CHECK'):
                continue
            
            # Extract column name and type
            column_match = re.match(r'(\w+)\s+([A-Za-z]+(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?)', line)
            if column_match:
                column_name = column_match.group(1)
                sql_type = column_match.group(2).upper()
                
                # Clean up type (remove size specifications)
                clean_type = re.sub(r'\(\s*\d+(?:\s*,\s*\d+)?\s*\)', '', sql_type).strip()
                columns[column_name] = clean_type
        
        return columns

    def get_python_type(self, sql_type: str) -> str:
        """
        Get Python type for a SQL type.
        
        Args:
            sql_type: SQL column type
            
        Returns:
            Python type annotation
        """
        # Clean up the type by removing size specifications and normalizing case
        clean_type = re.sub(r'\(\s*\d+(?:\s*,\s*\d+)?\s*\)', '', sql_type).upper().strip()
        
        # Try exact match first
        if clean_type in self._sql_type_mapping:
            return self._sql_type_mapping[clean_type]
        
        # Try case insensitive lookup
        for key, value in self._sql_type_mapping.items():
            if key.upper() == clean_type:
                return value
        
        # Fallback to default
        return self._sql_type_mapping.get('DEFAULT', 'Any')

    def get_column_type(self, table_name: str, column_name: str) -> str:
        """
        Get Python type for a specific table column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            Python type annotation
        """
        if table_name in self._table_schemas:
            sql_type = self._table_schemas[table_name].get(column_name)
            if sql_type:
                return self.get_python_type(sql_type)
        
        return 'Any'

    def load_schema(self, schema_file_path: str) -> None:
        """
        Load a schema file and populate the internal table schemas.
        
        Args:
            schema_file_path: Path to the schema file to load
        """
        schema_path = Path(schema_file_path)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        self._table_schemas = self.parse_schema_file(str(schema_path))

    def generate_types_file(self, *, output_path: str | None = None) -> str:
        """
        Generate the default SQL type mapping YAML file.
        
        Args:
            output_path: Optional path to save the types file. If None, saves as 'types.yaml' in current directory.
            
        Returns:
            Path to the generated types file
            
        Raises:
            OSError: If the file cannot be written
        """
        if output_path is None:
            output_path = "types.yaml"
            
        output_path = Path(output_path)
        
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get the default mapping
        default_mapping = self._get_default_mapping()
        
        # Write the YAML file with comments
        yaml_content = """# SQL Type to Python Type Mapping
# This file maps SQL column types to Python type annotations
# Customize this file for your specific database and requirements

"""
        
        # Group types by database for better organization
        sqlite_types = {
            'INTEGER': 'int', 'INT': 'int', 'BIGINT': 'int',
            'TEXT': 'str', 'VARCHAR': 'str', 'CHAR': 'str',
            'DECIMAL': 'float', 'REAL': 'float', 'FLOAT': 'float', 'DOUBLE': 'float',
            'BOOLEAN': 'bool', 'BOOL': 'bool',
            'TIMESTAMP': 'str', 'DATETIME': 'str', 'DATE': 'str',
            'BLOB': 'bytes'
        }
        
        postgresql_types = {
            'JSON': 'dict', 'JSONB': 'dict', 'UUID': 'str',
            'SERIAL': 'int', 'BIGSERIAL': 'int'
        }
        
        mysql_types = {
            'TINYINT': 'int', 'SMALLINT': 'int', 'MEDIUMINT': 'int',
            'LONGTEXT': 'str', 'ENUM': 'str'
        }
        
        mssql_types = {
            'BIT': 'bool', 'NUMERIC': 'float', 'MONEY': 'float', 'SMALLMONEY': 'float',
            'NCHAR': 'str', 'NVARCHAR': 'str', 'NTEXT': 'str',
            'BINARY': 'bytes', 'VARBINARY': 'bytes', 'IMAGE': 'bytes',
            'DATETIME2': 'str', 'SMALLDATETIME': 'str', 'TIME': 'str',
            'DATETIMEOFFSET': 'str', 'ROWVERSION': 'str', 'UNIQUEIDENTIFIER': 'str',
            'XML': 'str', 'SQL_VARIANT': 'Any'
        }
        
        oracle_types = {
            'NUMBER': 'float', 'VARCHAR2': 'str', 'NVARCHAR2': 'str',
            'CLOB': 'str', 'NCLOB': 'str', 'LONG': 'str',
            'RAW': 'bytes', 'ROWID': 'str', 'INTERVAL': 'str'
        }
        
        # Add SQLite types
        yaml_content += "# SQLite types\n"
        for sql_type, python_type in sorted(sqlite_types.items()):
            yaml_content += f"{sql_type}: {python_type}\n"
        
        yaml_content += "\n# PostgreSQL types\n"
        for sql_type, python_type in sorted(postgresql_types.items()):
            yaml_content += f"{sql_type}: {python_type}\n"
        
        yaml_content += "\n# MySQL types\n"
        for sql_type, python_type in sorted(mysql_types.items()):
            yaml_content += f"{sql_type}: {python_type}\n"
        
        yaml_content += "\n# MSSQL types\n"
        for sql_type, python_type in sorted(mssql_types.items()):
            yaml_content += f"{sql_type}: {python_type}\n"
        
        yaml_content += "\n# Oracle types\n"
        for sql_type, python_type in sorted(oracle_types.items()):
            yaml_content += f"{sql_type}: {python_type}\n"
        
        yaml_content += "\n# Default fallback for unknown types\nDEFAULT: Any\n"
        
        # Write the file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
        except OSError as e:
            raise OSError(f"Failed to write types file to {output_path}: {e}") from e
        
        return str(output_path)

    def load_schema_for_sql_file(self, sql_file_path: str, *, schema_file_path: str | None = None) -> None:
        """
        Load schema file for a given SQL file.
        
        Args:
            sql_file_path: Path to the SQL file
            schema_file_path: Optional path to the schema file. If None, looks for a .schema file
                             with the same stem as the SQL file.
        """
        if schema_file_path is None:
            # Default behavior: look for .schema file with same stem
            sql_path = Path(sql_file_path)
            schema_path = sql_path.with_suffix('.schema')
        else:
            schema_path = Path(schema_file_path)
        
        # Schema files are mandatory, so this should always exist
        self._table_schemas = self.parse_schema_file(str(schema_path))


