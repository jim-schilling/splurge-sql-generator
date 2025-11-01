"""
Edge case tests for the SchemaParser module to increase coverage.

Covers:
- YAML mapping loading fallbacks and validations
- Error propagation in parse_schema_file (UnicodeError, SplurgeSqlGeneratorOSError, SplurgeSqlGeneratorSqlValidationError)
- Explicit schema_file_path override in load_schema_for_sql_file
- Case-insensitive lookups in get_column_type
"""

import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator.exceptions import SplurgeSqlGeneratorFileError, SplurgeSqlGeneratorSqlValidationError
from splurge_sql_generator.schema_parser import SchemaParser


def test_yaml_non_string_values_and_missing_default():
    """Non-string mapping values are filtered and DEFAULT is added when missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_path = Path(temp_dir) / "types.yaml"
        # INTEGER has non-string value, should be filtered out; DEFAULT is missing
        yaml_content = """
INTEGER: 123
TEXT: str
"""
        yaml_path.write_text(yaml_content, encoding="utf-8")

        parser = SchemaParser(sql_type_mapping_file=str(yaml_path))

        # INTEGER entry should be filtered out (non-string); TEXT remains; DEFAULT added as Any
        assert "INTEGER" not in parser._sql_type_mapping
        assert parser._sql_type_mapping.get("TEXT") == "str"
        assert parser._sql_type_mapping.get("DEFAULT") == "Any"


def test_yaml_invalid_yaml_syntax_fallback():
    """Invalid YAML syntax falls back to default mapping."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_path = Path(temp_dir) / "bad.yaml"
        yaml_path.write_text("INTEGER: [unclosed", encoding="utf-8")

        parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
        # Should fall back to default mapping
        assert "INTEGER" in parser._sql_type_mapping
        assert parser._sql_type_mapping.get("DEFAULT") == "Any"


def test_yaml_not_dict_fallback():
    """YAML loading a non-dict value triggers fallback to default mapping."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_path = Path(temp_dir) / "not_dict.yaml"
        yaml_path.write_text("123", encoding="utf-8")

        parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
        assert "INTEGER" in parser._sql_type_mapping
        assert parser._sql_type_mapping.get("DEFAULT") == "Any"


def test_yaml_oserror_fallback():
    """Passing a directory as mapping file path causes OSError and fallback to default mapping."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use the directory itself as the file path to cause an OSError on open()
        parser = SchemaParser(sql_type_mapping_file=temp_dir)
        assert "INTEGER" in parser._sql_type_mapping
        assert parser._sql_type_mapping.get("DEFAULT") == "Any"


def test_yaml_default_override_affects_unknown_types():
    """Custom DEFAULT in YAML should be used for unknown types."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_path = Path(temp_dir) / "custom_default.yaml"
        yaml_path.write_text("DEFAULT: str\nTEXT: str\n", encoding="utf-8")

        parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
        # Unknown type should return the custom default (str), not Any
        assert parser.get_python_type("SOMETHING_UNKNOWN") == "str"


def test_parse_schema_file_unicode_decode_error():
    """Binary file with invalid UTF-8 should raise SplurgeSqlGeneratorFileError via safe_read_file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_file = Path(temp_dir) / "bad.schema"
        # Write invalid UTF-8 byte sequence: 0xFF is always invalid in UTF-8
        # as it would require continuation bytes that aren't present
        with open(bad_file, "wb") as f:
            f.write(b"\xff\xfe\xfd\xfc")

        parser = SchemaParser()
        with pytest.raises(SplurgeSqlGeneratorFileError):
            parser._parse_schema_file(str(bad_file))


def test_parse_schema_file_oserror_on_directory():
    """Passing a directory to parse_schema_file should raise SplurgeSqlGeneratorFileError."""
    from splurge_sql_generator.exceptions import SplurgeSqlGeneratorFileError

    with tempfile.TemporaryDirectory() as temp_dir:
        parser = SchemaParser()
        with pytest.raises(SplurgeSqlGeneratorFileError):
            parser._parse_schema_file(temp_dir)


def test_parse_schema_file_sql_validation_error_propagates():
    """Malformed CREATE TABLE with only table-level constraint should raise SplurgeSqlGeneratorSqlValidationError(."""
    with tempfile.TemporaryDirectory() as temp_dir:
        schema_path = Path(temp_dir) / "empty_body.schema"
        # Table has an identifier without a type, which results in no valid
        # column definitions; parse_table_columns will raise.
        schema_path.write_text(
            """
CREATE TABLE users (
  id
);
""",
            encoding="utf-8",
        )

        parser = SchemaParser()
        with pytest.raises(SplurgeSqlGeneratorSqlValidationError) as ctx:
            parser._parse_schema_file(str(schema_path))

        assert "No valid column definitions found in table body" in str(ctx.value)


def test_load_schema_for_sql_file_with_explicit_override():
    """Explicit schema_file_path override should be used instead of derived .schema."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        sql_file = temp_dir_path / "test.sql"
        sql_file.write_text("# TestClass\n#method\nSELECT 1;", encoding="utf-8")

        # Create a derived .schema file that should be ignored by override
        derived_schema = temp_dir_path / "test.schema"
        derived_schema.write_text(
            """
CREATE TABLE users (
  id INTEGER
);
""",
            encoding="utf-8",
        )

        # Create a custom schema to be used by override
        override_schema = temp_dir_path / "override.schema"
        override_schema.write_text(
            """
CREATE TABLE orders (
  order_id INTEGER,
  total DECIMAL(10,2)
);
""",
            encoding="utf-8",
        )

        parser = SchemaParser()
        parser.load_schema_for_sql_file(str(sql_file), schema_file_path=str(override_schema))

        assert "orders" in parser.table_schemas
        assert "users" not in parser.table_schemas
        assert parser.get_column_type("orders", "order_id") == "int"
        assert parser.get_column_type("orders", "total") == "float"


def test_get_column_type_case_insensitive_lookup():
    """Table and column lookups should be case-insensitive."""
    parser = SchemaParser()
    # Simulate loaded schema
    parser._table_schemas = {"users": {"id": "INTEGER", "name": "TEXT"}}

    assert parser.get_column_type("Users", "Name") == "str"
    assert parser.get_column_type("USERS", "ID") == "int"
