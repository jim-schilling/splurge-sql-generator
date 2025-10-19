"""
Python code generator for creating SQLAlchemy classes from SQL templates.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import splurge_safe_io.exceptions as safe_io_exc
from jinja2 import Environment, FileSystemLoader
from splurge_safe_io.safe_text_file_writer import SafeTextFileWriter, open_safe_text_writer

from splurge_sql_generator.exceptions import FileError, SqlValidationError
from splurge_sql_generator.schema_parser import SchemaParser
from splurge_sql_generator.sql_parser import SqlParser
from splurge_sql_generator.utils import to_snake_case

DOMAINS = ["code", "generator"]


class PythonCodeGenerator:
    """Generator for Python classes with SQLAlchemy methods using Jinja2 templates."""

    def __init__(
        self,
        *,
        sql_type_mapping_file: str | None = None,
        validate_parameters: bool = False,
    ) -> None:
        """
        Initialize the Python code generator.

        Args:
            sql_type_mapping_file: Optional path to custom SQL type mapping YAML file.
                If None, uses default "types.yaml"
            validate_parameters: Whether to validate SQL parameters against schema (default: False)
        """
        self._parser = SqlParser()
        self._schema_parser = SchemaParser(sql_type_mapping_file=sql_type_mapping_file or "types.yaml")
        self._validate_parameters = validate_parameters
        # Set up Jinja2 environment with templates directory
        template_dir = Path(__file__).parent / "templates"
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Preload template once for reuse
        self._template = self._jinja_env.get_template("python_class.j2")

    @property
    def parser(self) -> SqlParser:
        """Public read-only access to the SQL parser instance."""
        return self._parser

    @property
    def jinja_env(self) -> Environment:
        """Public read-only access to the Jinja environment."""
        return self._jinja_env

    def generate_class(
        self,
        sql_file_path: str,
        *,
        output_file_path: str | None = None,
        schema_file_path: Path | str,
    ) -> str:
        """
        Generate a Python class from a SQL file.

        Args:
            sql_file_path: Path to the SQL template file
            output_file_path: Optional path to save the generated Python file
            schema_file_path: Path to the schema file (required)

        Returns:
            Generated Python code as string

        Raises:
            FileNotFoundError: If the required schema file is missing
        """
        # Parse the SQL file first (this will catch validation errors like invalid class names)
        class_name, method_queries = self.parser.parse_file(sql_file_path)

        try:
            # Load schema
            schema_path = Path(schema_file_path)
            self._schema_parser.load_schema(schema_path)

        except safe_io_exc.SplurgeSafeIoPathValidationError as e:
            raise FileError(
                message=f"Schema file path is invalid: {schema_file_path}. Specify a schema file using the --schema option or ensure a corresponding .schema file exists.",
                details=str(e.message),
            ) from e
        except safe_io_exc.SplurgeSafeIoFileNotFoundError as e:
            raise FileError(
                message=f"Schema file not found: {schema_file_path}. Specify a schema file using the --schema option or ensure a corresponding .schema file exists.",
                details=str(e.message),
            ) from e
        except safe_io_exc.SplurgeSafeIoFilePermissionError as e:
            raise FileError(
                message=f"Permission denied reading schema file: {schema_file_path}. Specify a schema file using the --schema option or ensure a corresponding .schema file exists.",
                details=str(e.message),
            ) from e

        # Generate the Python code using template
        python_code = self._generate_python_code(class_name, method_queries, sql_file_path)

        # Save to file if output path provided
        if output_file_path:
            try:
                with open_safe_text_writer(output_file_path) as writer:
                    writer.write(python_code)
            except safe_io_exc.SplurgeSafeIoFileEncodingError as e:
                raise FileError(
                    message=f"Encoding error writing to file: {output_file_path}.", details=str(e.message)
                ) from e
            except safe_io_exc.SplurgeSafeIoFilePermissionError as e:
                raise FileError(
                    message=f"Permission denied writing to file: {output_file_path}.", details=str(e.message)
                ) from e
            except safe_io_exc.SplurgeSafeIoOsError as e:
                raise FileError(message=f"OS error writing to file: {output_file_path}.", details=str(e.message)) from e
            except safe_io_exc.SplurgeSafeIoFileOperationError as e:
                raise FileError(
                    message=f"File operation error writing to file: {output_file_path}.", details=str(e.message)
                ) from e
            except safe_io_exc.SplurgeSafeIoUnknownError as e:
                raise FileError(
                    message=f"Unknown error writing to file: {output_file_path}.", details=str(e.message)
                ) from e
        return python_code

    def _generate_python_code(
        self,
        class_name: str,
        method_queries: dict[str, str],
        file_path: str | None = None,
    ) -> str:
        """
        Generate Python class code from method queries using Jinja2 template.

        Args:
            class_name: Name of the class to generate
            method_queries: Dictionary mapping method names to SQL queries
            file_path: Optional file path for error context

        Returns:
            Generated Python code
        """
        # Prepare methods data for template
        methods: list[dict[str, Any]] = []
        for method_name, sql_query in method_queries.items():
            method_info = self.parser.get_method_info(sql_query)
            method_data = self._prepare_method_data(method_name, sql_query, method_info, file_path)
            methods.append(method_data)

        # Render template (preloaded)
        return str(self._template.render(class_name=class_name, methods=methods))

    @dataclass
    class _MethodData:
        """
        Internal dataclass for organizing method data for template rendering.

        Attributes:
            name: Method name
            parameters: Formatted parameter string for method signature
            parameters_list: List of parameter names
            param_mapping: Dictionary mapping SQL parameters to Python parameters
            param_types: Dictionary mapping parameter names to Python types
            return_type: Python return type annotation
            type: SQL query type (select, insert, update, delete, etc.)
            statement_type: Statement type (fetch or execute)
            is_fetch: Whether the statement returns rows
            sql_lines: SQL query split into lines for template rendering
        """

        name: str
        parameters: str
        parameters_list: list[str]
        param_mapping: dict[str, str]
        param_types: dict[str, str]
        return_type: str
        type: str
        statement_type: str
        is_fetch: bool
        sql_lines: list[str]

    def _prepare_method_data(
        self,
        method_name: str,
        sql_query: str,
        method_info: dict[str, Any],
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Prepare method data for template rendering.

        Args:
            method_name: Name of the method
            sql_query: SQL query string
            method_info: Analysis information about the method
            file_path: Optional file path for error context

        Returns:
            Dictionary with method data for template
        """
        # Validate parameters against schema if enabled
        if self._validate_parameters:
            self._validate_parameters_against_schema(sql_query, method_info["parameters"], file_path)

        # Generate method signature
        parameters = self._generate_method_signature(method_info["parameters"])

        # Prepare SQL lines for template
        sql_lines = sql_query.split("\n")

        # Prepare parameter mapping and types
        param_mapping: dict[str, str] = {}
        param_types: dict[str, str] = {}
        parameters_list: list[str] = []
        if method_info["parameters"]:
            for param in method_info["parameters"]:
                python_param = param  # Preserve original parameter name
                param_mapping[param] = python_param

                # Infer parameter type from schema
                param_types[param] = self._infer_parameter_type(sql_query, param)

                if python_param not in parameters_list:
                    parameters_list.append(python_param)

        data = self._MethodData(
            name=method_name,
            parameters=parameters,
            parameters_list=parameters_list,
            param_mapping=param_mapping,
            param_types=param_types,
            return_type="List[Row]" if method_info["is_fetch"] else "Result",
            type=method_info["type"],
            statement_type=method_info["statement_type"],
            is_fetch=method_info["is_fetch"],
            sql_lines=sql_lines,
        )

        # Jinja template expects a dict-like object; dataclass is easily serializable
        return {
            "name": data.name,
            "parameters": data.parameters,
            "parameters_list": data.parameters_list,
            "param_mapping": data.param_mapping,
            "param_types": data.param_types,
            "return_type": data.return_type,
            "type": data.type,
            "statement_type": data.statement_type,
            "is_fetch": data.is_fetch,
            "sql_lines": data.sql_lines,
        }

    def _generate_method_signature(self, parameters: list[str]) -> str:
        """
        Generate method signature with parameters.

        Args:
            parameters: List of parameter names

        Returns:
            Method signature string
        """
        if not parameters:
            return ""

        # Convert SQL parameters to Python parameters and remove duplicates
        python_params: list[str] = []
        seen_params: set[str] = set()
        for param in parameters:
            # Use original parameter name (preserve underscores)
            python_param = param
            if python_param not in seen_params:
                python_params.append(f"{python_param}: Any")
                seen_params.add(python_param)

        return ", ".join(python_params)

    def _extract_table_names(self, sql_query: str) -> list[str]:
        """
        Extract table names from SQL query using sql_helper.

        Args:
            sql_query: SQL query string

        Returns:
            List of table names referenced in the query (in lowercase)
        """
        # Use the SQL parser's table name extraction which leverages sql_helper
        return self._parser.get_table_names(sql_query)

    def _validate_parameters_against_schema(
        self,
        sql_query: str,
        parameters: list[str],
        file_path: str | None = None,
    ) -> None:
        """
        Validate that all SQL parameters exist in the loaded schema.

        Args:
            sql_query: SQL query string
            parameters: List of parameter names to validate
            file_path: Optional file path for error context

        Raises:
            SqlValidationError: If parameters don't match schema definitions
        """
        if not parameters:
            return

        # Extract table names from the SQL query
        table_names = self._extract_table_names(sql_query)

        if not table_names:
            # No tables found in query, can't validate parameters
            return

        # Check each parameter against the schema
        invalid_params = []
        for param in parameters:
            param_found = False
            for table_name in table_names:
                if (
                    table_name in self._schema_parser.table_schemas
                    and param in self._schema_parser.table_schemas[table_name]
                ):
                    param_found = True
                    break

            if not param_found:
                invalid_params.append(param)

        if invalid_params:
            file_context = f" in {file_path}" if file_path else ""
            tables_str = ", ".join(table_names)
            params_str = ", ".join(invalid_params)
            raise SqlValidationError(
                f"Parameters not found in schema{file_context}: {params_str}. "
                f"Referenced tables: {tables_str}. "
                f"Available columns: {self._get_available_columns(table_names)}"
            )

    def _infer_parameter_type(self, sql_query: str, parameter: str) -> str:
        """
        Infer the Python type for a SQL parameter based on the schema.

        Args:
            sql_query: SQL query string
            parameter: Parameter name to infer type for

        Returns:
            Python type annotation
        """
        # Extract table names from the SQL query
        table_names = self._extract_table_names(sql_query)

        if not table_names:
            return "Any"

        # First, try exact match with column names
        for table_name in table_names:
            if (
                table_name in self._schema_parser.table_schemas
                and parameter in self._schema_parser.table_schemas[table_name]
            ):
                sql_type = self._schema_parser.table_schemas[table_name][parameter]
                return self._schema_parser.get_python_type(sql_type)

        # If no exact match, try to infer from SQL context
        return self._infer_type_from_sql_context(sql_query, parameter, table_names)

    def _infer_type_from_sql_context(self, sql_query: str, parameter: str, table_names: list[str]) -> str:
        """
        Infer parameter type from SQL query context when parameter name doesn't match column names.

        Args:
            sql_query: SQL query string
            parameter: Parameter name to infer type for
            table_names: List of table names in the query

        Returns:
            Python type annotation
        """
        # Look for the parameter in WHERE clauses, SET clauses, etc.
        sql_upper = sql_query.upper()
        param_placeholder = f":{parameter}"

        # Check if parameter is used in WHERE clause with specific columns
        for table_name in table_names:
            if table_name not in self._schema_parser.table_schemas:
                continue

            table_schema = self._schema_parser.table_schemas[table_name]

            # Check each column in the table
            for column_name, sql_type in table_schema.items():
                # Look for patterns like "WHERE column = :parameter" or "SET column = :parameter"
                # Use regex patterns to handle whitespace variations
                patterns = [
                    rf"WHERE\s+{column_name}\s*=\s*{re.escape(param_placeholder)}",
                    rf"SET\s+{column_name}\s*=\s*{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s*<=\s*{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s*>=\s*{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s*>\s*{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s*<\s*{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s+LIKE\s+{re.escape(param_placeholder)}",
                    rf"WHERE\s+{column_name}\s+IN\s+{re.escape(param_placeholder)}",
                ]

                for pattern in patterns:
                    if re.search(pattern, sql_upper):
                        return self._schema_parser.get_python_type(sql_type)

        # If still no match, try common parameter name patterns
        return self._infer_type_from_parameter_name(parameter)

    def _infer_type_from_parameter_name(self, parameter: str) -> str:
        """
        Infer type from common parameter naming patterns.

        Args:
            parameter: Parameter name

        Returns:
            Python type annotation
        """
        parameter_lower = parameter.lower()

        # Common patterns for different types
        if any(suffix in parameter_lower for suffix in ["_id", "id"]):
            return "int"
        elif any(
            suffix in parameter_lower
            for suffix in [
                "_quantity",
                "quantity",
                "count",
                "amount",
                "number",
                "threshold",
            ]
        ):
            return "int"
        elif any(suffix in parameter_lower for suffix in ["_price", "price", "cost", "rate"]):
            return "float"
        elif any(suffix in parameter_lower for suffix in ["_name", "name", "title", "label"]):
            return "str"
        elif any(suffix in parameter_lower for suffix in ["_description", "description", "text", "content"]):
            return "str"
        elif any(suffix in parameter_lower for suffix in ["_term", "term", "search", "query"]):
            return "str"
        elif any(suffix in parameter_lower for suffix in ["_active", "active", "enabled", "is_"]):
            return "bool"

        return "Any"

    def _get_available_columns(self, table_names: list[str]) -> str:
        """
        Get a formatted string of available columns for the given tables.

        Args:
            table_names: List of table names

        Returns:
            Formatted string showing available columns
        """
        available_columns = []
        for table_name in table_names:
            if table_name in self._schema_parser.table_schemas:
                columns = list(self._schema_parser.table_schemas[table_name].keys())
                available_columns.append(f"{table_name}({', '.join(columns)})")

        return "; ".join(available_columns) if available_columns else "none"

    def generate_multiple_classes(
        self,
        sql_files: list[str],
        *,
        output_dir: str | None = None,
        schema_file_path: str,
    ) -> dict[str, str]:
        """
        Generate multiple Python classes from SQL files.

        Args:
            sql_files: List of SQL file paths
            output_dir: Optional directory to save generated files
            schema_file_path: Path to a shared schema file (required)

        Returns:
            Dictionary mapping class names to generated code

        Raises:
            FileNotFoundError: If any required schema file is missing
        """
        # Load shared schema file
        schema_path = Path(schema_file_path)
        if schema_path.exists():
            # Load the shared schema file
            self._schema_parser.load_schema(schema_file_path)
        else:
            # Schema file is required
            raise FileNotFoundError(
                f"Schema file required but not found: {schema_path}. "
                f"Specify a valid schema file using the --schema option."
            )

        generated_classes: dict[str, str] = {}

        for sql_file in sql_files:
            # Parse once per file and render directly to avoid duplicate parsing
            class_name, method_queries = self.parser.parse_file(sql_file)
            python_code = self._generate_python_code(class_name, method_queries)
            generated_classes[class_name] = python_code

            # Save to file if output directory provided
            if output_dir:
                # Ensure output directory exists
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                # Convert class name to snake_case for filename
                snake_case_name = to_snake_case(class_name)
                output_path = Path(output_dir) / f"{snake_case_name}.py"
                # safe_write_file(output_path, python_code)
                try:
                    writer = SafeTextFileWriter(output_path)
                    writer.write(python_code)
                finally:
                    writer.close()

        return generated_classes
