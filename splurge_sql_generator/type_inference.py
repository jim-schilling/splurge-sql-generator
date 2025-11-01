"""
Type inference for SQL parameters.

This module provides logic to infer Python types for SQL parameters based on
schema information, SQL context, and parameter naming patterns.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import re

DOMAINS = ["type", "inference"]


class ParameterTypeInferrer:
    """Infers Python types for SQL parameters."""

    def __init__(self, schema_parser) -> None:  # type: ignore[no-untyped-def]
        """
        Initialize the type inferrer.

        Args:
            schema_parser: SchemaParser instance with loaded table schemas
        """
        self._schema_parser = schema_parser

    def infer(self, sql_query: str, parameter: str) -> str:
        """
        Infer Python type for a SQL parameter using fallback chain.

        Tries three strategies in order:
        1. Exact match with column names in schema
        2. SQL context matching (WHERE/SET clauses)
        3. Parameter name heuristics

        Args:
            sql_query: SQL query string
            parameter: Parameter name to infer type for

        Returns:
            Python type annotation (str, int, float, bool, dict, Any)

        Examples:
            >>> # With schema loaded
            >>> inferrer.infer("SELECT * FROM users WHERE id = :id", "id")
            'int'
            >>> inferrer.infer("SELECT * FROM users WHERE name = :name", "name")
            'str'
        """
        # Extract table names from the SQL query
        table_names = self._get_table_names_from_sql(sql_query)

        if not table_names:
            return "Any"

        # First, try exact match with column names
        if type_result := self._exact_match(parameter, table_names):
            return type_result

        # Second, try SQL context match
        if type_result := self._sql_context_match(sql_query, parameter, table_names):
            return type_result

        # Finally, try name heuristics
        return self._name_heuristics(parameter)

    def _exact_match(self, parameter: str, table_names: list[str]) -> str | None:
        """
        Try to match parameter name to column name in schema.

        Args:
            parameter: Parameter name to match
            table_names: List of table names in the query

        Returns:
            Python type if match found, None otherwise
        """
        for table_name in table_names:
            if (
                table_name in self._schema_parser.table_schemas
                and parameter in self._schema_parser.table_schemas[table_name]
            ):
                sql_type = self._schema_parser.table_schemas[table_name][parameter]
                python_type = self._schema_parser.get_python_type(sql_type)
                return str(python_type) if python_type else None

        return None

    def _sql_context_match(self, sql_query: str, parameter: str, table_names: list[str]) -> str | None:
        """
        Try to infer type from SQL context (WHERE/SET clauses).

        Args:
            sql_query: SQL query string
            parameter: Parameter name to infer type for
            table_names: List of table names in the query

        Returns:
            Python type if context match found, None otherwise
        """
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
                        python_type = self._schema_parser.get_python_type(sql_type)
                        return str(python_type) if python_type else None

        return None

    def _name_heuristics(self, parameter: str) -> str:
        """
        Infer type from common parameter naming patterns.

        Args:
            parameter: Parameter name

        Returns:
            Python type annotation (default: "Any")
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

    def _get_table_names_from_sql(self, sql_query: str) -> list[str]:
        """
        Extract table names from SQL query.

        Args:
            sql_query: SQL query string

        Returns:
            List of table names (in lowercase)
        """
        from .sql_helper import extract_table_names

        try:
            return extract_table_names(sql_query)
        except Exception:
            # If extraction fails, return empty list
            return []
