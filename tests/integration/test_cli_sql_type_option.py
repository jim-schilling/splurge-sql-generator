"""
Tests for the CLI --types option functionality.
"""

import os
import shutil
import tempfile
import unittest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.schema_parser import SchemaParser
from tests.unit.test_utils import (
    temp_sql_files,
    assert_generated_code_structure,
    assert_method_parameters
)


class TestCLISqlTypeOption(unittest.TestCase):
    """Test cases for CLI --types option."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, PermissionError):
            pass

    def test_custom_sql_type_mapping_file(self):
        """Test that custom SQL type mapping file is used correctly."""
        # Create a custom SQL type mapping file
        custom_yaml_content = """
# Custom SQL Type to Python Type Mapping
CUSTOM_INT: int
CUSTOM_STRING: str
CUSTOM_FLOAT: float
DEFAULT: Any
"""
        custom_yaml_file = os.path.join(self.temp_dir, "custom_types.yaml")
        with open(custom_yaml_file, "w", encoding="utf-8") as f:
            f.write(custom_yaml_content)

        # Create a test SQL file
        sql_content = """
# TestClass

#test_method
SELECT id, name, value FROM test_table WHERE id = :custom_int;
"""
        sql_file = os.path.join(self.temp_dir, "test.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write(sql_content)

        # Create a schema file
        schema_content = """
CREATE TABLE test_table (
    id CUSTOM_INT PRIMARY KEY,
    name CUSTOM_STRING NOT NULL,
    value CUSTOM_FLOAT
);
"""
        schema_file = os.path.join(self.temp_dir, "test.schema")
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(schema_content)

        # Test that the custom mapping is used
        parser = SchemaParser(sql_type_mapping_file=custom_yaml_file)
        
        # Verify custom types are loaded
        self.assertEqual(parser.get_python_type("CUSTOM_INT"), "int")
        self.assertEqual(parser.get_python_type("CUSTOM_STRING"), "str")
        self.assertEqual(parser.get_python_type("CUSTOM_FLOAT"), "float")
        
        # Verify unknown types fall back to DEFAULT
        self.assertEqual(parser.get_python_type("UNKNOWN_TYPE"), "Any")

    def test_default_sql_type_mapping_when_not_specified(self):
        """Test that default SQL type mapping is used when not specified."""
        # Create a test SQL file
        sql_content = """
# TestClass

#test_method
SELECT id, name FROM test_table WHERE id = :id;
"""
        sql_file = os.path.join(self.temp_dir, "test.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write(sql_content)

        # Test that default mapping is used
        parser = SchemaParser()  # Should use default types.yaml
        
        # Verify default types are loaded
        self.assertEqual(parser.get_python_type("INTEGER"), "int")
        self.assertEqual(parser.get_python_type("TEXT"), "str")
        self.assertEqual(parser.get_python_type("DECIMAL"), "float")

    def test_custom_sql_type_mapping_in_code_generator(self):
        """Test that custom SQL type mapping is loaded but all parameters use Any type."""
        # Create a custom SQL type mapping file
        custom_yaml_content = """
# Custom SQL Type to Python Type Mapping
CUSTOM_INT: int
CUSTOM_STRING: str
DEFAULT: Any
"""
        custom_yaml_file = os.path.join(self.temp_dir, "custom_types.yaml")
        with open(custom_yaml_file, "w", encoding="utf-8") as f:
            f.write(custom_yaml_content)

        # Create test SQL and schema content
        sql_content = """# TestClass
#test_method
SELECT id, name FROM test_table WHERE id = :custom_int;
"""
        
        schema_content = """CREATE TABLE test_table (
    id CUSTOM_INT PRIMARY KEY,
    name CUSTOM_STRING NOT NULL
);
"""
        
        with temp_sql_files(sql_content, schema_content) as (sql_file, schema_file):
            # Test code generator with custom mapping
            generator = PythonCodeGenerator(sql_type_mapping_file=custom_yaml_file)
            
            # Generate code
            generated_code = generator.generate_class(sql_file, schema_file_path=schema_file)
            
            # Verify code structure
            assert_generated_code_structure(generated_code, "TestClass", ["test_method"])
            
            # Verify all parameters use Any type (no type inference)
            assert_method_parameters(generated_code, "test_method", ["custom_int"])
            
            # Verify the custom mapping file was loaded by checking schema parser
            self.assertEqual(generator._schema_parser.get_python_type("CUSTOM_INT"), "int")
            self.assertEqual(generator._schema_parser.get_python_type("CUSTOM_STRING"), "str")


if __name__ == "__main__":
    unittest.main()
