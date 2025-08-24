"""
Tests for the SchemaParser module.

These tests validate the behavior of the SchemaParser without using mocks,
focusing on real file operations and SQL parsing.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from splurge_sql_generator.schema_parser import SchemaParser
from test_utils import create_basic_schema, create_complex_schema


class TestSchemaParser(unittest.TestCase):
    """Test cases for SchemaParser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = SchemaParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files and directories
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_sql_type_mapping_default(self):
        """Test loading default SQL type mapping."""
        # Create a default sql_type.yaml file
        yaml_content = """
# SQL Type to Python Type Mapping
INTEGER: int
TEXT: str
DECIMAL: float
BOOLEAN: bool
TIMESTAMP: str
DEFAULT: Any
"""
        yaml_file = os.path.join(self.temp_dir, "sql_type.yaml")
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        parser = SchemaParser(yaml_file)
        mapping = parser._sql_type_mapping

        self.assertEqual(mapping["INTEGER"], "int")
        self.assertEqual(mapping["TEXT"], "str")
        self.assertEqual(mapping["DECIMAL"], "float")
        self.assertEqual(mapping["BOOLEAN"], "bool")
        self.assertEqual(mapping["TIMESTAMP"], "str")
        self.assertEqual(mapping["DEFAULT"], "Any")

    def test_load_sql_type_mapping_missing_file(self):
        """Test behavior when SQL type mapping file is missing."""
        # Should not raise an exception, should use default mapping
        parser = SchemaParser("nonexistent_file.yaml")
        
        # Should have some default mappings
        self.assertIn("INTEGER", parser._sql_type_mapping)
        self.assertIn("TEXT", parser._sql_type_mapping)
        self.assertIn("DEFAULT", parser._sql_type_mapping)

    def test_custom_yaml_mapping_case_insensitive(self):
        """Test case insensitive lookups with custom YAML mapping."""
        # Create a custom YAML file with mixed case
        yaml_content = """
# SQL Type to Python Type Mapping
Integer: int
Text: str
Decimal: float
Boolean: bool
Timestamp: str
Default: Any
"""
        yaml_file = os.path.join(self.temp_dir, "custom_sql_type.yaml")
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        parser = SchemaParser(yaml_file)
        
        # Test case insensitive lookups
        self.assertEqual(parser.get_python_type("INTEGER"), "int")
        self.assertEqual(parser.get_python_type("integer"), "int")
        self.assertEqual(parser.get_python_type("Integer"), "int")
        self.assertEqual(parser.get_python_type("TEXT"), "str")
        self.assertEqual(parser.get_python_type("text"), "str")
        self.assertEqual(parser.get_python_type("Text"), "str")
        self.assertEqual(parser.get_python_type("DECIMAL"), "float")
        self.assertEqual(parser.get_python_type("decimal"), "float")
        self.assertEqual(parser.get_python_type("Decimal"), "float")

    def test_parse_create_table_statement(self):
        """Test parsing CREATE TABLE statements."""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Parse the SQL content
        tables = self.parser._parse_schema_content(sql)
        
        # Check that table schema was parsed
        self.assertIn("users", tables)
        schema = tables["users"]
        
        # Check column types
        self.assertEqual(schema["id"], "INTEGER")
        self.assertEqual(schema["username"], "TEXT")
        self.assertEqual(schema["email"], "TEXT")
        self.assertEqual(schema["password_hash"], "TEXT")
        self.assertEqual(schema["status"], "TEXT")
        self.assertEqual(schema["created_at"], "TIMESTAMP")
        self.assertEqual(schema["updated_at"], "TIMESTAMP")

    def test_parse_create_table_with_complex_types(self):
        """Test parsing CREATE TABLE with complex SQL types."""
        sql = """
        CREATE TABLE products (
            id BIGINT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            metadata JSON,
            created_date DATE,
            updated_time DATETIME
        );
        """
        
        tables = self.parser._parse_schema_content(sql)
        schema = tables["products"]
        
        # Check that complex types are parsed correctly
        self.assertEqual(schema["id"], "BIGINT")
        self.assertEqual(schema["name"], "VARCHAR")
        self.assertEqual(schema["price"], "DECIMAL")
        self.assertEqual(schema["is_active"], "BOOLEAN")
        self.assertEqual(schema["metadata"], "JSON")
        self.assertEqual(schema["created_date"], "DATE")
        self.assertEqual(schema["updated_time"], "DATETIME")

    def test_parse_create_table_with_unknown_type(self):
        """Test parsing CREATE TABLE with unknown SQL type."""
        sql = """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            custom_field CUSTOM_TYPE,
            known_field TEXT
        );
        """
        
        tables = self.parser._parse_schema_content(sql)
        schema = tables["test_table"]
        
        # Unknown type should be parsed as-is (regex strips _TYPE part)
        self.assertEqual(schema["id"], "INTEGER")
        self.assertEqual(schema["custom_field"], "CUSTOM")  # Unknown type preserved (without _TYPE)
        self.assertEqual(schema["known_field"], "TEXT")

    def test_parse_schema_file(self):
        """Test parsing a complete schema file."""
        schema_content = """
        -- Test schema file
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            total DECIMAL(10,2),
            status TEXT DEFAULT 'pending'
        );
        """
        
        schema_file = os.path.join(self.temp_dir, "test.schema")
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(schema_content)
        
        tables = self.parser.parse_schema_file(schema_file)
        
        # Check that both tables were parsed
        self.assertIn("users", tables)
        self.assertIn("orders", tables)
        
        # Check users table schema
        users_schema = tables["users"]
        self.assertEqual(users_schema["id"], "INTEGER")
        self.assertEqual(users_schema["name"], "TEXT")
        self.assertEqual(users_schema["email"], "TEXT")
        
        # Check orders table schema
        orders_schema = tables["orders"]
        self.assertEqual(orders_schema["order_id"], "INTEGER")
        self.assertEqual(orders_schema["user_id"], "INTEGER")
        self.assertEqual(orders_schema["total"], "DECIMAL")
        self.assertEqual(orders_schema["status"], "TEXT")

    def test_parse_schema_file_with_comments(self):
        """Test parsing schema file with comments and whitespace."""
        schema_content = """
        -- This is a comment
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,  -- Primary key
            name TEXT NOT NULL,      -- User's full name
            email TEXT UNIQUE        -- Unique email address
        );
        
        -- Another table
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price DECIMAL(10,2)
        );
        """
        
        schema_file = os.path.join(self.temp_dir, "commented.schema")
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(schema_content)
        
        tables = self.parser.parse_schema_file(schema_file)
        
        # Should still parse correctly despite comments
        self.assertIn("users", tables)
        self.assertIn("products", tables)

    def test_parse_schema_file_missing(self):
        """Test parsing non-existent schema file."""
        missing_file = os.path.join(self.temp_dir, "missing.schema")
        
        # Should not raise an exception
        result = self.parser.parse_schema_file(missing_file)
        
        # Should return empty dict
        self.assertEqual(result, {})

    def test_get_column_type(self):
        """Test getting column type for various SQL types."""
        # Test basic types
        self.assertEqual(self.parser.get_python_type("INTEGER"), "int")
        self.assertEqual(self.parser.get_python_type("TEXT"), "str")
        self.assertEqual(self.parser.get_python_type("DECIMAL"), "float")
        self.assertEqual(self.parser.get_python_type("BOOLEAN"), "bool")
        
        # Test with size/precision specifications
        self.assertEqual(self.parser.get_python_type("VARCHAR(255)"), "str")
        self.assertEqual(self.parser.get_python_type("DECIMAL(10,2)"), "float")
        self.assertEqual(self.parser.get_python_type("INT(11)"), "int")
        
        # Test unknown type
        self.assertEqual(self.parser.get_python_type("UNKNOWN_TYPE"), "Any")
        
        # Test case insensitive lookups
        self.assertEqual(self.parser.get_python_type("integer"), "int")
        self.assertEqual(self.parser.get_python_type("Integer"), "int")
        self.assertEqual(self.parser.get_python_type("INTEGER"), "int")
        self.assertEqual(self.parser.get_python_type("text"), "str")
        self.assertEqual(self.parser.get_python_type("Text"), "str")
        self.assertEqual(self.parser.get_python_type("TEXT"), "str")
        self.assertEqual(self.parser.get_python_type("decimal"), "float")
        self.assertEqual(self.parser.get_python_type("Decimal"), "float")
        self.assertEqual(self.parser.get_python_type("DECIMAL"), "float")
        self.assertEqual(self.parser.get_python_type("boolean"), "bool")
        self.assertEqual(self.parser.get_python_type("Boolean"), "bool")
        self.assertEqual(self.parser.get_python_type("BOOLEAN"), "bool")

    def test_mssql_types(self):
        """Test MSSQL-specific type mappings."""
        # Test MSSQL numeric types
        self.assertEqual(self.parser.get_python_type("BIT"), "bool")
        self.assertEqual(self.parser.get_python_type("TINYINT"), "int")
        self.assertEqual(self.parser.get_python_type("SMALLINT"), "int")
        self.assertEqual(self.parser.get_python_type("INT"), "int")
        self.assertEqual(self.parser.get_python_type("BIGINT"), "int")
        self.assertEqual(self.parser.get_python_type("NUMERIC"), "float")
        self.assertEqual(self.parser.get_python_type("MONEY"), "float")
        self.assertEqual(self.parser.get_python_type("SMALLMONEY"), "float")
        
        # Test MSSQL string types
        self.assertEqual(self.parser.get_python_type("NCHAR"), "str")
        self.assertEqual(self.parser.get_python_type("NVARCHAR"), "str")
        self.assertEqual(self.parser.get_python_type("NTEXT"), "str")
        
        # Test MSSQL binary types
        self.assertEqual(self.parser.get_python_type("BINARY"), "bytes")
        self.assertEqual(self.parser.get_python_type("VARBINARY"), "bytes")
        self.assertEqual(self.parser.get_python_type("IMAGE"), "bytes")
        
        # Test MSSQL date/time types
        self.assertEqual(self.parser.get_python_type("DATETIME2"), "str")
        self.assertEqual(self.parser.get_python_type("SMALLDATETIME"), "str")
        self.assertEqual(self.parser.get_python_type("TIME"), "str")
        self.assertEqual(self.parser.get_python_type("DATETIMEOFFSET"), "str")
        
        # Test MSSQL special types
        self.assertEqual(self.parser.get_python_type("ROWVERSION"), "str")
        self.assertEqual(self.parser.get_python_type("UNIQUEIDENTIFIER"), "str")
        self.assertEqual(self.parser.get_python_type("XML"), "str")
        self.assertEqual(self.parser.get_python_type("SQL_VARIANT"), "Any")

    def test_oracle_types(self):
        """Test Oracle-specific type mappings."""
        # Test Oracle numeric types
        self.assertEqual(self.parser.get_python_type("NUMBER"), "float")
        
        # Test Oracle string types
        self.assertEqual(self.parser.get_python_type("CLOB"), "str")
        self.assertEqual(self.parser.get_python_type("NCLOB"), "str")
        self.assertEqual(self.parser.get_python_type("LONG"), "str")
        self.assertEqual(self.parser.get_python_type("VARCHAR2"), "str")
        self.assertEqual(self.parser.get_python_type("NVARCHAR2"), "str")
        
        # Test Oracle binary types
        self.assertEqual(self.parser.get_python_type("RAW"), "bytes")
        
        # Test Oracle special types
        self.assertEqual(self.parser.get_python_type("ROWID"), "str")
        self.assertEqual(self.parser.get_python_type("INTERVAL"), "str")



    def test_load_schema_for_sql_file(self):
        """Test loading schema file for a given SQL file."""
        # Create a schema file
        schema_content = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
        
        schema_file = os.path.join(self.temp_dir, "test.schema")
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(schema_content)
        
        # Create a corresponding SQL file
        sql_file = os.path.join(self.temp_dir, "test.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write("# TestClass\n#method\nSELECT 1;")
        
        # Load schema for the SQL file
        self.parser.load_schema_for_sql_file(sql_file)
        
        # Check that schema was loaded
        self.assertIn("users", self.parser._table_schemas)
        self.assertEqual(self.parser._table_schemas["users"]["id"], "INTEGER")
        self.assertEqual(self.parser._table_schemas["users"]["name"], "TEXT")

    def test_load_schema_for_sql_file_no_schema(self):
        """Test loading schema when no schema file exists."""
        # Create a SQL file without a corresponding schema file
        sql_file = os.path.join(self.temp_dir, "test.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write("# TestClass\n#method\nSELECT 1;")
        
        # Load schema for the SQL file
        self.parser.load_schema_for_sql_file(sql_file)
        
        # Should not have loaded any schemas
        self.assertEqual(len(self.parser._table_schemas), 0)

    def test_clear_schemas(self):
        """Test clearing all loaded schemas."""
        # Load some schemas
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
        tables = self.parser._parse_schema_content(sql)
        self.parser._table_schemas = tables
        
        # Verify schema was loaded
        self.assertIn("users", self.parser._table_schemas)
        
        # Clear schemas
        self.parser._table_schemas.clear()
        
        # Verify schemas were cleared
        self.assertEqual(len(self.parser._table_schemas), 0)

    def test_get_column_type_for_table(self):
        """Test getting column type for a specific table column."""
        # Load a schema
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        );
        """
        tables = self.parser._parse_schema_content(sql)
        self.parser._table_schemas = tables
        
        # Get column types
        self.assertEqual(self.parser.get_column_type("users", "id"), "int")
        self.assertEqual(self.parser.get_column_type("users", "name"), "str")
        self.assertEqual(self.parser.get_column_type("users", "email"), "str")
        
        # Test getting non-existent column
        self.assertEqual(self.parser.get_column_type("users", "non_existent"), "Any")
        
        # Test getting column from non-existent table
        self.assertEqual(self.parser.get_column_type("non_existent", "id"), "Any")

    def test_get_all_table_names(self):
        """Test getting all loaded table names."""
        # Load multiple schemas
        sql1 = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
        
        sql2 = """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
        
        tables1 = self.parser._parse_schema_content(sql1)
        tables2 = self.parser._parse_schema_content(sql2)
        
        # Combine the tables
        self.parser._table_schemas = {**tables1, **tables2}
        
        # Get all table names
        table_names = list(self.parser._table_schemas.keys())
        
        # Should contain both table names
        self.assertIn("users", table_names)
        self.assertIn("products", table_names)
        self.assertEqual(len(table_names), 2)

    def test_parse_schema_file_with_multiple_statements(self):
        """Test parsing schema file with multiple CREATE TABLE statements."""
        schema_content = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            total DECIMAL(10,2)
        );
        
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER
        );
        """
        
        schema_file = os.path.join(self.temp_dir, "multiple.schema")
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(schema_content)
        
        tables = self.parser.parse_schema_file(schema_file)
        
        # Check that all tables were parsed
        self.assertIn("users", tables)
        self.assertIn("orders", tables)
        self.assertIn("order_items", tables)
        
        # Check some column types
        self.assertEqual(tables["users"]["id"], "INTEGER")
        self.assertEqual(tables["orders"]["total"], "DECIMAL")
        self.assertEqual(tables["order_items"]["quantity"], "INTEGER")


if __name__ == "__main__":
    unittest.main()
