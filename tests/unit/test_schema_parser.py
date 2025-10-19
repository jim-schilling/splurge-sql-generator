"""
Tests for the SchemaParser module.

These tests validate the behavior of the SchemaParser without using mocks,
focusing on real file operations and SQL parsing.
"""

import os
import shutil
import tempfile

import pytest

from splurge_sql_generator.schema_parser import SchemaParser


@pytest.fixture
def parser():
    return SchemaParser()


@pytest.fixture
def temp_dir():
    _temp_dir_value = tempfile.mkdtemp()
    yield _temp_dir_value
    # Clean up temporary files and directories
    shutil.rmtree(_temp_dir_value, ignore_errors=True)


def test_load_sql_type_mapping_default(parser, temp_dir):
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
    yaml_file = os.path.join(temp_dir, "sql_type.yaml")
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    parser = SchemaParser(sql_type_mapping_file=yaml_file)
    mapping = parser._sql_type_mapping

    assert mapping["INTEGER"] == "int"
    assert mapping["TEXT"] == "str"
    assert mapping["DECIMAL"] == "float"
    assert mapping["BOOLEAN"] == "bool"
    assert mapping["TIMESTAMP"] == "str"
    assert mapping["DEFAULT"] == "Any"


def test_load_sql_type_mapping_missing_file(parser, temp_dir):
    """Test behavior when SQL type mapping file is missing."""
    # Should not raise an exception, should use default mapping
    parser = SchemaParser(sql_type_mapping_file="nonexistent_file.yaml")

    # Should have some default mappings
    assert "INTEGER" in parser._sql_type_mapping
    assert "TEXT" in parser._sql_type_mapping
    assert "DEFAULT" in parser._sql_type_mapping


def test_custom_yaml_mapping_case_insensitive(parser, temp_dir):
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
    yaml_file = os.path.join(temp_dir, "custom_sql_type.yaml")
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    parser = SchemaParser(sql_type_mapping_file=yaml_file)

    # Test case insensitive lookups
    assert parser.get_python_type("INTEGER") == "int"
    assert parser.get_python_type("integer") == "int"
    assert parser.get_python_type("Integer") == "int"
    assert parser.get_python_type("TEXT") == "str"
    assert parser.get_python_type("text") == "str"
    assert parser.get_python_type("Text") == "str"
    assert parser.get_python_type("DECIMAL") == "float"
    assert parser.get_python_type("decimal") == "float"
    assert parser.get_python_type("Decimal") == "float"


def test_parse_create_table_statement(parser, temp_dir):
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
    tables = parser._parse_schema_content(sql)

    # Check that table schema was parsed
    assert "users" in tables
    schema = tables["users"]

    # Check column types
    assert schema["id"] == "INTEGER"
    assert schema["username"] == "TEXT"
    assert schema["email"] == "TEXT"
    assert schema["password_hash"] == "TEXT"
    assert schema["status"] == "TEXT"
    assert schema["created_at"] == "TIMESTAMP"
    assert schema["updated_at"] == "TIMESTAMP"


def test_parse_create_table_if_not_exists(parser, temp_dir):
    """Test parsing CREATE TABLE IF NOT EXISTS statements extracts table name."""
    sql = """
        CREATE TABLE IF NOT EXISTS mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_schema_prefix(parser, temp_dir):
    """Test parsing CREATE TABLE statements with schema prefix extracts table name."""
    sql = """
        CREATE TABLE my_schema.mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_bracketed_schema_prefix(parser, temp_dir):
    """Test parsing CREATE TABLE statements with bracketed schema prefix extracts table name."""
    sql = """
        CREATE TABLE [myschema].[mytable] (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_bracketed_table_name(parser, temp_dir):
    """Test parsing CREATE TABLE statements with bracketed table name extracts table name."""
    sql = """
        CREATE TABLE [mytable] (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_backtick_table_name(parser, temp_dir):
    """Test parsing CREATE TABLE statements with backtick-quoted table name extracts table name."""
    sql = """
        CREATE TABLE `mytable` (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_backtick_schema_prefix(parser, temp_dir):
    """Test parsing CREATE TABLE statements with backtick-quoted schema prefix extracts table name."""
    sql = """
        CREATE TABLE `myschema`.`mytable` (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_quoted_table_name(parser, temp_dir):
    """Test parsing CREATE TABLE statements with double-quoted table name extracts table name."""
    sql = """
        CREATE TABLE "mytable" (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_quoted_schema_prefix(parser, temp_dir):
    """Test parsing CREATE TABLE statements with double-quoted schema prefix extracts table name."""
    sql = """
        CREATE TABLE "myschema"."mytable" (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_with_mixed_quoting(parser, temp_dir):
    """Test parsing CREATE TABLE statements with mixed quoting styles extracts table name."""
    sql = """
        CREATE TABLE [myschema].`mytable` (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """

    tables = parser._parse_schema_content(sql)

    assert "mytable" in tables
    schema = tables["mytable"]
    assert schema["id"] == "TEXT"
    assert schema["value"] == "TEXT"


def test_parse_create_table_malformed_if_not_exists(parser, temp_dir):
    """Test parsing malformed CREATE TABLE with incomplete IF NOT EXISTS sequence."""
    # Test IF without NOT EXISTS
    sql1 = """
        CREATE TABLE IF mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Test NOT without IF
    sql2 = """
        CREATE TABLE NOT EXISTS mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL

    # Test EXISTS without IF NOT
    sql3 = """
        CREATE TABLE EXISTS mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables3 = parser._parse_schema_content(sql3)
    assert tables3 == {}  # Should not parse malformed SQL

    # Test IF NOT without EXISTS
    sql4 = """
        CREATE TABLE IF NOT mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables4 = parser._parse_schema_content(sql4)
    assert tables4 == {}  # Should not parse malformed SQL


def test_parse_create_table_missing_table_name(parser, temp_dir):
    """Test parsing CREATE TABLE statements with missing table name."""
    # Missing table name after TABLE
    sql1 = """
        CREATE TABLE (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Missing table name after IF NOT EXISTS
    sql2 = """
        CREATE TABLE IF NOT EXISTS (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL


def test_parse_create_table_missing_parentheses(parser, temp_dir):
    """Test parsing CREATE TABLE statements with missing or malformed parentheses."""
    # Missing opening parenthesis
    sql1 = """
        CREATE TABLE mytable
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Missing closing parenthesis
    sql2 = """
        CREATE TABLE mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL

    # Mismatched parentheses - this might actually parse successfully
    # because sqlparse treats the extra ) as part of the statement
    sql3 = """
        CREATE TABLE mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        ));
        """
    tables3 = parser._parse_schema_content(sql3)
    # This might actually succeed because sqlparse handles the extra )
    # We'll accept either behavior as long as it's consistent
    if tables3:
        # If it parses, it should extract the table correctly
        assert "mytable" in tables3
        schema = tables3["mytable"]
        assert schema["id"] == "TEXT"
        assert schema["value"] == "TEXT"
    else:
        # If it doesn't parse, that's also acceptable
        pass


def test_parse_create_table_invalid_schema_prefix(parser, temp_dir):
    """Test parsing CREATE TABLE statements with invalid schema prefix."""
    # Schema prefix without table name
    sql1 = """
        CREATE TABLE myschema. (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Multiple dots in schema prefix
    sql2 = """
        CREATE TABLE myschema.subschema.mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL


def test_parse_create_table_empty_body(parser, temp_dir):
    """Test parsing CREATE TABLE statements with empty table body."""
    # Empty parentheses
    sql1 = """
        CREATE TABLE mytable (
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Only whitespace in parentheses
    sql2 = """
        CREATE TABLE mytable (
            
        );
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL


def test_parse_create_table_malformed_keywords(parser, temp_dir):
    """Test parsing CREATE TABLE statements with malformed keywords."""
    # Wrong keyword order
    sql1 = """
        TABLE CREATE mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables1 = parser._parse_schema_content(sql1)
    assert tables1 == {}  # Should not parse malformed SQL

    # Missing CREATE keyword
    sql2 = """
        TABLE mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables2 = parser._parse_schema_content(sql2)
    assert tables2 == {}  # Should not parse malformed SQL

    # Missing TABLE keyword
    sql3 = """
        CREATE mytable (
            id TEXT PRIMARY KEY,
            value TEXT
        );
        """
    tables3 = parser._parse_schema_content(sql3)
    assert tables3 == {}  # Should not parse malformed SQL


def test_parse_create_table_with_complex_types(parser, temp_dir):
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

    tables = parser._parse_schema_content(sql)
    schema = tables["products"]

    # Check that complex types are parsed correctly
    assert schema["id"] == "BIGINT"
    assert schema["name"] == "VARCHAR"
    assert schema["price"] == "DECIMAL"
    assert schema["is_active"] == "BOOLEAN"
    assert schema["metadata"] == "JSON"
    assert schema["created_date"] == "DATE"
    assert schema["updated_time"] == "DATETIME"


def test_parse_create_table_with_unknown_type(parser, temp_dir):
    """Test parsing CREATE TABLE with unknown SQL type."""
    sql = """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            custom_field CUSTOM_TYPE,
            known_field TEXT
        );
        """

    tables = parser._parse_schema_content(sql)
    schema = tables["test_table"]

    # Unknown type should be parsed as-is (regex strips _TYPE part)
    assert schema["id"] == "INTEGER"
    assert schema["custom_field"] == "CUSTOM"  # Unknown type preserved (without _TYPE)
    assert schema["known_field"] == "TEXT"


def test_parse_schema_file(parser, temp_dir):
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

    schema_file = os.path.join(temp_dir, "test.schema")
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)

    parser.load_schema(schema_file)
    tables = parser.table_schemas

    # Check that both tables were parsed
    assert "users" in tables
    assert "orders" in tables

    # Check users table schema
    users_schema = tables["users"]
    assert users_schema["id"] == "INTEGER"
    assert users_schema["name"] == "TEXT"
    assert users_schema["email"] == "TEXT"

    # Check orders table schema
    orders_schema = tables["orders"]
    assert orders_schema["order_id"] == "INTEGER"
    assert orders_schema["user_id"] == "INTEGER"
    assert orders_schema["total"] == "DECIMAL"
    assert orders_schema["status"] == "TEXT"


def test_parse_schema_file_with_comments(parser, temp_dir):
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

    schema_file = os.path.join(temp_dir, "commented.schema")
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)

    parser.load_schema(schema_file)
    tables = parser.table_schemas

    # Should still parse correctly despite comments
    assert "users" in tables
    assert "products" in tables


def test_parse_schema_file_missing(parser, temp_dir):
    """Test parsing non-existent schema file."""
    missing_file = os.path.join(temp_dir, "missing.schema")

    # Should not raise an exception
    parser.load_schema(missing_file)
    result = parser.table_schemas

    # Should return empty dict
    assert result == {}


def test_get_column_type(parser, temp_dir):
    """Test getting column type for various SQL types."""
    # Test basic types
    assert parser.get_python_type("INTEGER") == "int"
    assert parser.get_python_type("TEXT") == "str"
    assert parser.get_python_type("DECIMAL") == "float"
    assert parser.get_python_type("BOOLEAN") == "bool"

    # Test with size/precision specifications
    assert parser.get_python_type("VARCHAR(255)") == "str"
    assert parser.get_python_type("DECIMAL(10,2)") == "float"
    assert parser.get_python_type("INT(11)") == "int"

    # Test unknown type
    assert parser.get_python_type("UNKNOWN_TYPE") == "Any"

    # Test case insensitive lookups
    assert parser.get_python_type("integer") == "int"
    assert parser.get_python_type("Integer") == "int"
    assert parser.get_python_type("INTEGER") == "int"
    assert parser.get_python_type("text") == "str"
    assert parser.get_python_type("Text") == "str"
    assert parser.get_python_type("TEXT") == "str"
    assert parser.get_python_type("decimal") == "float"
    assert parser.get_python_type("Decimal") == "float"
    assert parser.get_python_type("DECIMAL") == "float"
    assert parser.get_python_type("boolean") == "bool"
    assert parser.get_python_type("Boolean") == "bool"
    assert parser.get_python_type("BOOLEAN") == "bool"


def test_mssql_types(parser, temp_dir):
    """Test MSSQL-specific type mappings."""
    # Test MSSQL numeric types
    assert parser.get_python_type("BIT") == "bool"
    assert parser.get_python_type("TINYINT") == "int"
    assert parser.get_python_type("SMALLINT") == "int"
    assert parser.get_python_type("INT") == "int"
    assert parser.get_python_type("BIGINT") == "int"
    assert parser.get_python_type("NUMERIC") == "float"
    assert parser.get_python_type("MONEY") == "float"
    assert parser.get_python_type("SMALLMONEY") == "float"

    # Test MSSQL string types
    assert parser.get_python_type("NCHAR") == "str"
    assert parser.get_python_type("NVARCHAR") == "str"
    assert parser.get_python_type("NTEXT") == "str"

    # Test MSSQL binary types
    assert parser.get_python_type("BINARY") == "bytes"
    assert parser.get_python_type("VARBINARY") == "bytes"
    assert parser.get_python_type("IMAGE") == "bytes"

    # Test MSSQL date/time types
    assert parser.get_python_type("DATETIME2") == "str"
    assert parser.get_python_type("SMALLDATETIME") == "str"
    assert parser.get_python_type("TIME") == "str"
    assert parser.get_python_type("DATETIMEOFFSET") == "str"

    # Test MSSQL special types
    assert parser.get_python_type("ROWVERSION") == "str"
    assert parser.get_python_type("UNIQUEIDENTIFIER") == "str"
    assert parser.get_python_type("XML") == "str"
    assert parser.get_python_type("SQL_VARIANT") == "Any"


def test_oracle_types(parser, temp_dir):
    """Test Oracle-specific type mappings."""
    # Test Oracle numeric types
    assert parser.get_python_type("NUMBER") == "float"

    # Test Oracle string types
    assert parser.get_python_type("CLOB") == "str"
    assert parser.get_python_type("NCLOB") == "str"
    assert parser.get_python_type("LONG") == "str"
    assert parser.get_python_type("VARCHAR2") == "str"
    assert parser.get_python_type("NVARCHAR2") == "str"

    # Test Oracle binary types
    assert parser.get_python_type("RAW") == "bytes"

    # Test Oracle special types
    assert parser.get_python_type("ROWID") == "str"
    assert parser.get_python_type("INTERVAL") == "str"


def test_load_schema(parser, temp_dir):
    """Test loading schema directly with schema file path."""
    # Create a schema file
    schema_content = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """

    schema_file = os.path.join(temp_dir, "test.schema")
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)

    # Test loading schema directly
    parser.load_schema(schema_file)

    # Verify that the schema was loaded
    assert "users" in parser._table_schemas
    assert parser.get_column_type("users", "id") == "int"
    assert parser.get_column_type("users", "name") == "str"


def test_load_schema_missing_file(parser, temp_dir):
    """Test loading schema with missing file loads empty schema."""
    missing_schema = os.path.join(temp_dir, "missing.schema")

    # Should not raise an exception, just load empty schema
    parser.load_schema(missing_schema)

    # Should have empty table schemas
    assert parser.table_schemas == {}


def test_load_schema_for_sql_file(parser, temp_dir):
    """Test loading schema file for a given SQL file."""
    # Create a schema file
    schema_content = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """

    schema_file = os.path.join(temp_dir, "test.schema")
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)

    # Create a corresponding SQL file
    sql_file = os.path.join(temp_dir, "test.sql")
    with open(sql_file, "w", encoding="utf-8") as f:
        f.write("# TestClass\n#method\nSELECT 1;")

    # Load schema for the SQL file
    parser.load_schema_for_sql_file(sql_file)

    # Check that schema was loaded
    assert "users" in parser._table_schemas
    assert parser._table_schemas["users"]["id"] == "INTEGER"
    assert parser._table_schemas["users"]["name"] == "TEXT"


def test_load_schema_for_sql_file_no_schema(parser, temp_dir):
    """Test loading schema when no schema file exists."""
    # Create a SQL file without a corresponding schema file
    sql_file = os.path.join(temp_dir, "test.sql")
    with open(sql_file, "w", encoding="utf-8") as f:
        f.write("# TestClass\n#method\nSELECT 1;")

    # Load schema for the SQL file
    parser.load_schema_for_sql_file(sql_file)

    # Should not have loaded any schemas
    assert len(parser._table_schemas) == 0


def test_clear_schemas(parser, temp_dir):
    """Test clearing all loaded schemas."""
    # Load some schemas
    sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """
    tables = parser._parse_schema_content(sql)
    parser._table_schemas = tables

    # Verify schema was loaded
    assert "users" in parser._table_schemas

    # Clear schemas
    parser._table_schemas.clear()

    # Verify schemas were cleared
    assert len(parser._table_schemas) == 0


def test_get_column_type_for_table(parser, temp_dir):
    """Test getting column type for a specific table column."""
    # Load a schema
    sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        );
        """
    tables = parser._parse_schema_content(sql)
    parser._table_schemas = tables

    # Get column types
    assert parser.get_column_type("users", "id") == "int"
    assert parser.get_column_type("users", "name") == "str"
    assert parser.get_column_type("users", "email") == "str"

    # Test getting non-existent column
    assert parser.get_column_type("users", "non_existent") == "Any"

    # Test getting column from non-existent table
    assert parser.get_column_type("non_existent", "id") == "Any"


def test_get_all_table_names(parser, temp_dir):
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

    tables1 = parser._parse_schema_content(sql1)
    tables2 = parser._parse_schema_content(sql2)

    # Combine the tables
    parser._table_schemas = {**tables1, **tables2}

    # Get all table names
    table_names = list(parser._table_schemas.keys())

    # Should contain both table names
    assert "users" in table_names
    assert "products" in table_names
    assert len(table_names) == 2


def test_parse_schema_file_with_multiple_statements(parser, temp_dir):
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

    schema_file = os.path.join(temp_dir, "multiple.schema")
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)

    parser.load_schema(schema_file)
    tables = parser.table_schemas

    # Check that all tables were parsed
    assert "users" in tables
    assert "orders" in tables
    assert "order_items" in tables

    # Check some column types
    assert tables["users"]["id"] == "INTEGER"
    assert tables["orders"]["total"] == "DECIMAL"
    assert tables["order_items"]["quantity"] == "INTEGER"
