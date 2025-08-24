"""
Tests for parameter validation functionality.

This module tests the parameter validation feature that ensures SQL parameters
map to existing table/column combinations in the loaded schema.
"""

import tempfile
import unittest
from pathlib import Path

from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.errors import SqlValidationError


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = PythonCodeGenerator(validate_parameters=True)

    def test_valid_parameters_pass_validation(self):
        """Test that valid parameters pass validation."""
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            # This should not raise an exception
            code = self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            self.assertIn("class TestClass", code)
            self.assertIn("def get_user", code)
            self.assertIn("def create_user", code)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_invalid_parameters_raise_error(self):
        """Test that invalid parameters raise SqlValidationError."""
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            with self.assertRaises(SqlValidationError) as cm:
                self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            
            error_msg = str(cm.exception)
            self.assertIn("user_id", error_msg)
            self.assertIn("users", error_msg)
            self.assertIn("Available columns", error_msg)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_multiple_invalid_parameters_raise_error(self):
        """Test that multiple invalid parameters are reported."""
        sql = """# TestClass
#create_user
INSERT INTO users (name, email, status) VALUES (:name, :email, :status);
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            with self.assertRaises(SqlValidationError) as cm:
                self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            
            error_msg = str(cm.exception)
            self.assertIn("status", error_msg)
            self.assertIn("Available columns", error_msg)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_validation_disabled_by_default(self):
        """Test that parameter validation is disabled by default."""
        # Create generator without validation
        generator = PythonCodeGenerator(validate_parameters=False)
        
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            # This should not raise an exception even with invalid parameters
            code = generator.generate_class(sql_fname, schema_file_path=schema_fname)
            self.assertIn("class TestClass", code)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_validation_with_multiple_tables(self):
        """Test parameter validation with multiple tables."""
        sql = """# TestClass
#get_user_orders
SELECT u.name, o.order_date 
FROM users u 
JOIN orders o ON u.id = o.user_id 
    WHERE u.id = :user_id AND o.status = :status;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    order_date DATE,
    status TEXT
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            # This should not raise an exception - both parameters exist in schema
            code = self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            self.assertIn("class TestClass", code)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_validation_with_nonexistent_table(self):
        """Test parameter validation when table doesn't exist in schema."""
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :id;
        """
        schema = """CREATE TABLE other_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            with self.assertRaises(SqlValidationError) as cm:
                self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            
            error_msg = str(cm.exception)
            self.assertIn("id", error_msg)
            self.assertIn("users", error_msg)
            self.assertIn("Available columns: none", error_msg)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_validation_with_no_parameters(self):
        """Test that validation passes when there are no parameters."""
        sql = """# TestClass
#get_all_users
SELECT * FROM users;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            # This should not raise an exception
            code = self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            self.assertIn("class TestClass", code)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()

    def test_validation_with_no_tables_in_query(self):
        """Test that validation passes when query has no table references."""
        sql = """# TestClass
#get_version
SELECT 1 as version;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
        """
        
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)
        
        try:
            # This should not raise an exception - no tables to validate against
            code = self.generator.generate_class(sql_fname, schema_file_path=schema_fname)
            self.assertIn("class TestClass", code)
        finally:
            Path(sql_fname).unlink()
            Path(schema_fname).unlink()


if __name__ == "__main__":
    unittest.main()
