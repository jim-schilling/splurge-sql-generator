"""
Schema parser for SQL table definitions.

This module parses SQL schema files to extract column type information
for accurate Python type inference in generated code.

Copyright (c) 2025 Jim Schilling

This module is licensed under the MIT License.
"""

import logging
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from splurge_sql_generator.exceptions import FileError, SqlValidationError
from splurge_sql_generator.file_utils import SafeTextFileIoAdapter
from splurge_sql_generator.sql_helper import (
    extract_create_table_statements,
    parse_table_columns,
)
from splurge_sql_generator.utils import clean_sql_type

DOMAINS = ["schema", "parser"]


# Module-level constant: Default SQL type to Python type mapping
_DEFAULT_SQL_TYPE_MAPPING: dict[str, str] = {
    # SQLite types
    "INTEGER": "int",
    "INT": "int",
    "BIGINT": "int",
    "TEXT": "str",
    "VARCHAR": "str",
    "CHAR": "str",
    "DECIMAL": "float",
    "REAL": "float",
    "FLOAT": "float",
    "DOUBLE": "float",
    "BOOLEAN": "bool",
    "BOOL": "bool",
    "TIMESTAMP": "str",
    "DATETIME": "str",
    "DATE": "str",
    "BLOB": "bytes",
    # PostgreSQL types
    "JSON": "dict",
    "JSONB": "dict",
    "UUID": "str",
    "SERIAL": "int",
    "BIGSERIAL": "int",
    # MySQL types
    "TINYINT": "int",
    "SMALLINT": "int",
    "MEDIUMINT": "int",
    "LONGTEXT": "str",
    "ENUM": "str",
    # MSSQL types
    "BIT": "bool",
    "NUMERIC": "float",
    "MONEY": "float",
    "SMALLMONEY": "float",
    "NCHAR": "str",
    "NVARCHAR": "str",
    "NTEXT": "str",
    "BINARY": "bytes",
    "VARBINARY": "bytes",
    "IMAGE": "bytes",
    "DATETIME2": "str",
    "SMALLDATETIME": "str",
    "TIME": "str",
    "DATETIMEOFFSET": "str",
    "ROWVERSION": "str",
    "UNIQUEIDENTIFIER": "str",
    "XML": "str",
    "SQL_VARIANT": "Any",
    # Oracle types
    "NUMBER": "float",
    "VARCHAR2": "str",
    "NVARCHAR2": "str",
    "CLOB": "str",
    "NCLOB": "str",
    "LONG": "str",
    "RAW": "bytes",
    "ROWID": "str",
    "INTERVAL": "str",
    "DEFAULT": "Any",
}


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
        self._table_schemas: dict[str, dict[str, str]] = {}

    @property
    def table_schemas(self) -> dict[str, dict[str, str]]:
        """Public read-only access to the table schemas."""
        return self._table_schemas

    def _load_sql_type_mapping(self, mapping_file: str) -> dict[str, str]:
        """
        Load SQL type to Python type mapping from YAML file.

        Args:
            mapping_file: Path to the mapping file

        Returns:
            Dictionary mapping SQL types to Python types

        Raises:
            ValueError: If the loaded YAML is not a dictionary or is missing required keys
        """
        mapping_path = None
        try:
            mapping_path = Path(mapping_file)
            if mapping_path.exists():
                file_io = SafeTextFileIoAdapter()
                content = file_io.read_text(mapping_path, encoding="utf-8")
                loaded_mapping = yaml.safe_load(content)

                # Validate the loaded mapping
                if not isinstance(loaded_mapping, dict):
                    raise ValueError(
                        f"YAML file '{mapping_file}' must contain a dictionary, got {type(loaded_mapping).__name__}"
                    )

                # Validate that all values are strings
                invalid_entries: list[str] = []
                for key, value in loaded_mapping.items():
                    if not isinstance(value, str):
                        invalid_entries.append(f"{key}: {type(value).__name__}")

                if invalid_entries:
                    self._logger.warning(
                        f"YAML file '{mapping_file}' contains non-string values: {', '.join(invalid_entries)}. "
                        "These entries will be ignored."
                    )
                    # Filter out non-string values
                    loaded_mapping = {k: v for k, v in loaded_mapping.items() if isinstance(v, str)}

                # Ensure DEFAULT key exists
                if "DEFAULT" not in loaded_mapping:
                    self._logger.warning(
                        f"YAML file '{mapping_file}' is missing 'DEFAULT' key. "
                        "Adding 'DEFAULT: Any' as fallback for unknown types."
                    )
                    loaded_mapping["DEFAULT"] = "Any"

                self._logger.info(f"Successfully loaded {len(loaded_mapping)} type mappings from '{mapping_file}'")
                return loaded_mapping
            else:
                # Return default mapping if file doesn't exist
                self._logger.info(f"Type mapping file '{mapping_file}' not found, using default mappings")
                return self._get_default_mapping()

        except FileError as e:
            path_str = str(mapping_path) if mapping_path else mapping_file
            self._logger.warning(f"Error reading SQL type mapping file: {path_str}: {str(e.message)}")
            return self._get_default_mapping()
        except yaml.YAMLError as e:
            path_str = str(mapping_path) if mapping_path else mapping_file
            self._logger.warning(f"Invalid YAML syntax in SQL type mapping file: {path_str}: {str(e)}")
            return self._get_default_mapping()
        except Exception as e:
            path_str = str(mapping_path) if mapping_path else mapping_file
            self._logger.warning(f"Unexpected error reading SQL type mapping file: {path_str}: {str(e)}")
            return self._get_default_mapping()

    def _get_default_mapping(self) -> dict[str, str]:
        """
        Get default SQL type to Python type mapping.

        Returns:
            Copy of default mapping dictionary to prevent external mutation
        """
        return _DEFAULT_SQL_TYPE_MAPPING.copy()

    def _parse_schema_file(self, schema_file_path: Path | str) -> dict[str, dict[str, str]]:
        """
        Parse a SQL schema file and extract column type information.

        Args:
            schema_file_path: Path to the schema file

        Returns:
            Dictionary mapping table names to column type mappings

        Raises:
            FileError: If the schema file cannot be read
            SqlValidationError: If the SQL content is malformed and cannot be parsed
        Note:
            If the schema file does not exist, an empty dictionary is returned.
        """
        try:
            file_io = SafeTextFileIoAdapter()
            schema_content = file_io.read_text(schema_file_path)
            return self._parse_schema_content(schema_content)

        except FileError as e:
            # Check if it's a "not found" error - we return empty dict for those
            if "not found" in str(e.message).lower():
                return {}
            # Re-raise other FileErrors
            raise

    def _parse_schema_content(self, content: str) -> dict[str, dict[str, str]]:
        """
        Parse schema content and extract table column information.

        Args:
            content: SQL schema content

        Returns:
            Dictionary mapping table names to column type mappings

        Raises:
            SqlValidationError: If sqlparse fails to parse CREATE TABLE statements
        """
        tables: dict[str, dict[str, str]] = {}

        # Use sqlparse to extract CREATE TABLE statements
        create_tables = extract_create_table_statements(content)

        for table_name, table_body in create_tables:
            # Parse column definitions
            columns = self._parse_table_columns(table_body)
            tables[table_name] = columns

        return tables

    def _parse_table_columns(self, table_body: str) -> dict[str, str]:
        """
        Parse column definitions from table body using sqlparse.

        Args:
            table_body: Table body content between parentheses

        Returns:
            Dictionary mapping column names to SQL types
        """
        # Use the sqlparse-based column parsing function
        return parse_table_columns(table_body)

    def get_python_type(self, sql_type: str) -> str:
        """
        Get Python type for a SQL type.

        Args:
            sql_type: SQL column type

        Returns:
            Python type annotation
        """
        # Clean up the type by removing size specifications and normalizing case
        clean_type = clean_sql_type(sql_type).upper().strip()

        # Try exact match first
        if clean_type in self._sql_type_mapping:
            return self._sql_type_mapping[clean_type]

        # Try case insensitive lookup
        for key, value in self._sql_type_mapping.items():
            if key.upper() == clean_type:
                return value

        # Fallback to default
        default_type = self._sql_type_mapping.get("DEFAULT", "Any")
        if default_type == "Any":
            self._logger.debug(f"Unknown SQL type '{sql_type}' (cleaned: '{clean_type}'), using 'Any'")
        else:
            self._logger.debug(
                f"Unknown SQL type '{sql_type}' (cleaned: '{clean_type}'), using default: '{default_type}'"
            )

        return default_type

    def get_column_type(self, table_name: str, column_name: str) -> str:
        """
        Get Python type for a specific table column.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            Python type annotation
        """
        # Normalize table and column names to lowercase for consistent lookup
        table_name_lower = table_name.lower()
        column_name_lower = column_name.lower()

        if table_name_lower in self._table_schemas:
            sql_type = self._table_schemas[table_name_lower].get(column_name_lower)
            if sql_type:
                return self.get_python_type(sql_type)
            else:
                self._logger.debug(
                    f"Column '{column_name}' not found in table '{table_name}' (available columns: {list(self._table_schemas[table_name_lower].keys())})"
                )
        else:
            self._logger.debug(
                f"Table '{table_name}' not found in schema (available tables: {list(self._table_schemas.keys())})"
            )

        return "Any"

    def load_schema(self, schema_file_path: Path | str) -> None:
        """
        Load a schema file and populate the internal table schemas with error recovery.

        Args:
            schema_file_path: Path to the schema file to load

        Raises:
            FileError: If the schema file cannot be read (re-raised after logging)
            SqlValidationError: If the SQL content is malformed and cannot be parsed (re-raised after logging)

        Note:
            If the schema file does not exist, an empty schema will be loaded.
            Non-fatal errors will be logged as warnings with graceful degradation.
        """
        try:
            self._table_schemas = dict[str, dict[str, str]]()
            self._table_schemas = self._parse_schema_file(schema_file_path)
            self._logger.info(
                f"Successfully loaded schema from '{str(schema_file_path)}' with {len(self._table_schemas)} tables"
            )
        except FileError as e:
            self._logger.error(f"Failed to load schema from '{str(schema_file_path)}': {str(e)}")
            # Preserve empty schema and re-raise for explicit error handling
            raise
        except SqlValidationError as e:
            self._logger.error(f"SQL validation error in schema file '{str(schema_file_path)}': {str(e)}")
            # Re-raise validation errors - they indicate malformed SQL that needs attention
            raise
        except Exception as e:
            self._logger.error(
                f"Unexpected error loading schema from '{str(schema_file_path)}': {type(e).__name__}: {str(e)}"
            )
            raise

    def generate_types_file(self, *, output_path: Path | str | None = None) -> str:
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

        # Write the YAML file with comments
        yaml_content = """# SQL Type to Python Type Mapping
# This file maps SQL column types to Python type annotations
# Customize this file for your specific database and requirements

"""

        # Group types by database for better organization (derived from _DEFAULT_SQL_TYPE_MAPPING)
        sqlite_types = {
            "INTEGER": "int",
            "INT": "int",
            "BIGINT": "int",
            "TEXT": "str",
            "VARCHAR": "str",
            "CHAR": "str",
            "DECIMAL": "float",
            "REAL": "float",
            "FLOAT": "float",
            "DOUBLE": "float",
            "BOOLEAN": "bool",
            "BOOL": "bool",
            "TIMESTAMP": "str",
            "DATETIME": "str",
            "DATE": "str",
            "BLOB": "bytes",
        }

        postgresql_types = {
            "JSON": "dict",
            "JSONB": "dict",
            "UUID": "str",
            "SERIAL": "int",
            "BIGSERIAL": "int",
        }

        mysql_types = {
            "TINYINT": "int",
            "SMALLINT": "int",
            "MEDIUMINT": "int",
            "LONGTEXT": "str",
            "ENUM": "str",
        }

        mssql_types = {
            "BIT": "bool",
            "NUMERIC": "float",
            "MONEY": "float",
            "SMALLMONEY": "float",
            "NCHAR": "str",
            "NVARCHAR": "str",
            "NTEXT": "str",
            "BINARY": "bytes",
            "VARBINARY": "bytes",
            "IMAGE": "bytes",
            "DATETIME2": "str",
            "SMALLDATETIME": "str",
            "TIME": "str",
            "DATETIMEOFFSET": "str",
            "ROWVERSION": "str",
            "UNIQUEIDENTIFIER": "str",
            "XML": "str",
            "SQL_VARIANT": "Any",
        }

        oracle_types = {
            "NUMBER": "float",
            "VARCHAR2": "str",
            "NVARCHAR2": "str",
            "CLOB": "str",
            "NCLOB": "str",
            "LONG": "str",
            "RAW": "bytes",
            "ROWID": "str",
            "INTERVAL": "str",
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

        try:
            file_io = SafeTextFileIoAdapter()
            file_io.write_text(output_path, yaml_content)
            self._logger.info(f"Successfully generated types file: '{str(output_path)}'")
        except FileError as e:
            # Re-raise FileError with original message
            raise FileError(
                message=f"Error writing types file: {str(output_path)}.", details=str(e.message)
            ) from e

        return str(output_path)

    def load_schema_for_sql_file(
        self, sql_file_path: Path | str, *, schema_file_path: Path | str | None = None
    ) -> None:
        """
        Load schema file for a given SQL file.

        Args:
            sql_file_path: Path to the SQL file
            schema_file_path: Optional path to the schema file. If None, looks for a .schema file
                             with the same stem as the SQL file.

        Raises:
            FileError: If the schema file cannot be read
            SqlValidationError: If the SQL content is malformed and cannot be parsed
        """
        if schema_file_path is None:
            # Default behavior: look for .schema file with same stem
            sql_path = Path(sql_file_path)
            schema_path = sql_path.with_suffix(".schema")
            self._logger.info(
                f"Looking for schema file: '{str(schema_path)}' (derived from SQL file: '{str(sql_file_path)}')"
            )
        else:
            schema_path = Path(schema_file_path)
            self._logger.info(f"Using specified schema file: '{str(schema_path)}' for SQL file: '{str(sql_file_path)}'")

        # Load schema file (may be empty if file doesn't exist)
        try:
            self._table_schemas = self._parse_schema_file(str(schema_path))
            if len(self._table_schemas) > 0:
                self._logger.info(
                    f"Successfully loaded schema from '{str(schema_path)}' with {len(self._table_schemas)} tables for SQL file '{str(sql_file_path)}'"
                )
            else:
                self._logger.warning(
                    f"No schema found for SQL file '{str(sql_file_path)}'. Schema file '{str(schema_path)}' is empty or missing."
                )
        except (FileError, SqlValidationError) as e:
            self._logger.error(
                f"Failed to load schema from '{str(schema_path)}' for SQL file '{str(sql_file_path)}': {str(e)}"
            )
            raise
