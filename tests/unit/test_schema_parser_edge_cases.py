"""
Edge case tests for the SchemaParser module to increase coverage.

Covers:
- YAML mapping loading fallbacks and validations
- Error propagation in parse_schema_file (UnicodeDecodeError, OSError, SqlValidationError)
- Explicit schema_file_path override in load_schema_for_sql_file
- Case-insensitive lookups in get_column_type
"""

import tempfile
import unittest
from pathlib import Path

from splurge_sql_generator.schema_parser import SchemaParser
from splurge_sql_generator.errors import SqlValidationError


class TestSchemaParserEdgeCases(unittest.TestCase):
    def test_yaml_non_string_values_and_missing_default(self):
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
            self.assertNotIn("INTEGER", parser._sql_type_mapping)
            self.assertEqual(parser._sql_type_mapping.get("TEXT"), "str")
            self.assertEqual(parser._sql_type_mapping.get("DEFAULT"), "Any")

    def test_yaml_invalid_yaml_syntax_fallback(self):
        """Invalid YAML syntax falls back to default mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "bad.yaml"
            yaml_path.write_text("INTEGER: [unclosed", encoding="utf-8")

            parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
            # Should fall back to default mapping
            self.assertIn("INTEGER", parser._sql_type_mapping)
            self.assertEqual(parser._sql_type_mapping.get("DEFAULT"), "Any")

    def test_yaml_not_dict_fallback(self):
        """YAML loading a non-dict value triggers fallback to default mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "not_dict.yaml"
            yaml_path.write_text("123", encoding="utf-8")

            parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
            self.assertIn("INTEGER", parser._sql_type_mapping)
            self.assertEqual(parser._sql_type_mapping.get("DEFAULT"), "Any")

    def test_yaml_oserror_fallback(self):
        """Passing a directory as mapping file path causes OSError and fallback to default mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use the directory itself as the file path to cause an OSError on open()
            parser = SchemaParser(sql_type_mapping_file=temp_dir)
            self.assertIn("INTEGER", parser._sql_type_mapping)
            self.assertEqual(parser._sql_type_mapping.get("DEFAULT"), "Any")

    def test_yaml_default_override_affects_unknown_types(self):
        """Custom DEFAULT in YAML should be used for unknown types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "custom_default.yaml"
            yaml_path.write_text("DEFAULT: str\nTEXT: str\n", encoding="utf-8")

            parser = SchemaParser(sql_type_mapping_file=str(yaml_path))
            # Unknown type should return the custom default (str), not Any
            self.assertEqual(parser.get_python_type("SOMETHING_UNKNOWN"), "str")

    def test_parse_schema_file_unicode_decode_error(self):
        """Binary file with invalid UTF-8 should raise UnicodeDecodeError via safe_read_file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_file = Path(temp_dir) / "bad.schema"
            with open(bad_file, "wb") as f:
                f.write(b"\xff\xfe\xfa\x00\x81")

            parser = SchemaParser()
            with self.assertRaises(UnicodeDecodeError):
                parser.parse_schema_file(str(bad_file))

    def test_parse_schema_file_oserror_on_directory(self):
        """Passing a directory to parse_schema_file should raise OSError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = SchemaParser()
            with self.assertRaises(OSError):
                parser.parse_schema_file(temp_dir)

    def test_parse_schema_file_sql_validation_error_propagates(self):
        """Malformed CREATE TABLE with only table-level constraint should raise SqlValidationError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_path = Path(temp_dir) / "empty_body.schema"
            # Table has an identifier without a type, which results in no valid
            # column definitions; parse_table_columns will raise.
            schema_path.write_text("""
CREATE TABLE users (
  id
);
""", encoding="utf-8")

            parser = SchemaParser()
            with self.assertRaises(SqlValidationError) as ctx:
                parser.parse_schema_file(str(schema_path))

            self.assertIn("SQL validation error in schema file", str(ctx.exception))

    def test_load_schema_for_sql_file_with_explicit_override(self):
        """Explicit schema_file_path override should be used instead of derived .schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            sql_file = temp_dir_path / "test.sql"
            sql_file.write_text("# TestClass\n#method\nSELECT 1;", encoding="utf-8")

            # Create a derived .schema file that should be ignored by override
            derived_schema = temp_dir_path / "test.schema"
            derived_schema.write_text("""
CREATE TABLE users (
  id INTEGER
);
""", encoding="utf-8")

            # Create a custom schema to be used by override
            override_schema = temp_dir_path / "override.schema"
            override_schema.write_text("""
CREATE TABLE orders (
  order_id INTEGER,
  total DECIMAL(10,2)
);
""", encoding="utf-8")

            parser = SchemaParser()
            parser.load_schema_for_sql_file(str(sql_file), schema_file_path=str(override_schema))

            self.assertIn("orders", parser.table_schemas)
            self.assertNotIn("users", parser.table_schemas)
            self.assertEqual(parser.get_column_type("orders", "order_id"), "int")
            self.assertEqual(parser.get_column_type("orders", "total"), "float")

    def test_get_column_type_case_insensitive_lookup(self):
        """Table and column lookups should be case-insensitive."""
        parser = SchemaParser()
        # Simulate loaded schema
        parser._table_schemas = {
            "users": {"id": "INTEGER", "name": "TEXT"}
        }

        self.assertEqual(parser.get_column_type("Users", "Name"), "str")
        self.assertEqual(parser.get_column_type("USERS", "ID"), "int")


if __name__ == "__main__":
    unittest.main()


