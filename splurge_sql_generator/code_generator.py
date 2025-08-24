"""
Python code generator for creating SQLAlchemy classes from SQL templates.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from splurge_sql_generator.errors import SqlValidationError
from splurge_sql_generator.schema_parser import SchemaParser
from splurge_sql_generator.sql_parser import SqlParser


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
        schema_file_path: str,
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
        
        # Load schema
        schema_path = Path(schema_file_path)
        
        if schema_path.exists():
            # Load schema if it exists
            self._schema_parser.load_schema(schema_file_path)
        else:
            # Schema files are required
            raise FileNotFoundError(
                f"Schema file required but not found: {schema_path}. "
                f"Specify a schema file using the --schema option or ensure a corresponding .schema file exists."
            )

        # Generate the Python code using template
        python_code = self._generate_python_code(class_name, method_queries, sql_file_path)

        # Save to file if output path provided
        if output_file_path:
            try:
                Path(output_file_path).write_text(
                    python_code,
                    encoding="utf-8",
                )
            except OSError as e:
                raise OSError(
                    f"Error writing Python file {output_file_path}: {e}"
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
        return self._template.render(class_name=class_name, methods=methods)

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
            self._validate_parameters_against_schema(
                sql_query, 
                method_info["parameters"], 
                file_path
            )
        
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
                
                # All parameters use Any type (no type inference implemented)
                param_types[param] = "Any"
                
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
        Extract table names from SQL query.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of table names referenced in the query (in lowercase)
        """
        table_names = []
        
        # Extract table names from different SQL clauses
        # FROM clause
        from_pattern = r'\bFROM\s+(\w+)'
        from_matches = re.findall(from_pattern, sql_query, re.IGNORECASE)
        table_names.extend([match.lower() for match in from_matches])
        
        # UPDATE clause
        update_pattern = r'\bUPDATE\s+(\w+)'
        update_matches = re.findall(update_pattern, sql_query, re.IGNORECASE)
        table_names.extend([match.lower() for match in update_matches])
        
        # INSERT INTO clause
        insert_pattern = r'\bINSERT\s+INTO\s+(\w+)'
        insert_matches = re.findall(insert_pattern, sql_query, re.IGNORECASE)
        table_names.extend([match.lower() for match in insert_matches])
        
        # JOIN clauses
        join_pattern = r'\bJOIN\s+(\w+)'
        join_matches = re.findall(join_pattern, sql_query, re.IGNORECASE)
        table_names.extend([match.lower() for match in join_matches])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(table_names))

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
                if (table_name in self._schema_parser.table_schemas and 
                    param in self._schema_parser.table_schemas[table_name]):
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

    def _to_snake_case(self, class_name: str) -> str:
        """
        Convert PascalCase class name to snake_case filename.
        
        Args:
            class_name: PascalCase class name (e.g., 'UserRepository')
            
        Returns:
            Snake case filename (e.g., 'user_repository')
        """
        # Insert underscore before capital letters, then convert to lowercase
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        return snake_case

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
                snake_case_name = self._to_snake_case(class_name)
                output_path = Path(output_dir) / f"{snake_case_name}.py"
                try:
                    output_path.write_text(
                        python_code,
                        encoding="utf-8",
                    )
                except OSError as e:
                    raise OSError(
                        f"Error writing Python file {output_path}: {e}"
                    ) from e

        return generated_classes


