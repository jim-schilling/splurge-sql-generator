import ast
import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.sql_parser import SqlParser
from test_utils import (
    temp_sql_files,
    temp_multiple_sql_files,
    create_basic_schema,
    create_dummy_schema,
    create_complex_schema,
    assert_generated_code_structure,
    assert_method_parameters
)


class TestPythonCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = PythonCodeGenerator()
        self.parser = SqlParser()

    def test_generate_class_and_methods(self):
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        
        with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            assert_generated_code_structure(code, "TestClass", ["get_user", "create_user"])
            assert_method_parameters(code, "get_user", ["user_id"])
            assert_method_parameters(code, "create_user", ["name", "email"])

    def test_generate_class_output_file(self):
        sql = """# TestClass
#get_one
SELECT 1;
        """
        schema = """CREATE TABLE dummy (
    id INTEGER PRIMARY KEY
);
        """
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        schema_fname = Path(sql_fname).with_suffix('.schema')
        with open(schema_fname, "w") as f:
            f.write(schema)
        py_fd, py_fname = tempfile.mkstemp(suffix=".py")
        os.close(py_fd)
        try:
            code = self.generator.generate_class(sql_fname, output_file_path=py_fname, schema_file_path=schema_fname)
            self.assertTrue(os.path.exists(py_fname))
            with open(py_fname, "r") as f:
                content = f.read()
                self.assertIn("class TestClass", content)
                self.assertIn("def get_one", content)
        finally:
            os.remove(sql_fname)
            os.remove(schema_fname)
            os.remove(py_fname)

    def test_generate_multiple_classes(self):
        sql_files = [
            ("""# ClassA
#get_a
SELECT 1;
            """, create_dummy_schema("dummy1")),
            ("""# ClassB
#get_b
SELECT 2;
            """, create_dummy_schema("dummy2"))
        ]
        
        with temp_multiple_sql_files(sql_files) as file_paths:
            sql_file_paths = [sql_path for sql_path, _ in file_paths]
            schema_file_paths = [schema_path for _, schema_path in file_paths]
            # Use the first schema file as the shared schema
            result = self.generator.generate_multiple_classes(sql_file_paths, schema_file_path=schema_file_paths[0])
            
            self.assertEqual(len(result), 2)
            self.assertIn("ClassA", result)
            self.assertIn("ClassB", result)
            assert_generated_code_structure(result["ClassA"], "ClassA", ["get_a"])
            assert_generated_code_structure(result["ClassB"], "ClassB", ["get_b"])

    def test_generate_class_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_class("nonexistent_file.sql", schema_file_path="nonexistent.schema")

    def test_method_docstring_generation(self):
        # Test that the template correctly generates docstrings for different method types
        # Create a simple test case and verify the generated code contains expected docstring elements

        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
#get_all
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
            fname = f.name
        schema_fname = Path(fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)

        try:
            code = self.generator.generate_class(fname, schema_file_path=schema_fname)

            # Test method with parameters
            self.assertIn("Select operation: get_user", code)
            self.assertIn("Statement type: fetch", code)
            self.assertIn("Args:", code)
            self.assertIn("connection: SQLAlchemy database connection", code)
            self.assertIn("user_id: Parameter for user_id", code)
            self.assertIn("List of result rows", code)

            # Test method with multiple parameters
            self.assertIn("Insert operation: create_user", code)
            self.assertIn("Statement type: execute", code)
            self.assertIn("name: Parameter for name", code)
            self.assertIn("email: Parameter for email", code)
            self.assertIn("SQLAlchemy Result object", code)

            # Test method with no SQL parameters (only connection)
            self.assertIn("Select operation: get_all", code)
            self.assertIn("Statement type: fetch", code)
            self.assertIn("Args:", code)
            self.assertIn("connection: SQLAlchemy database connection", code)
            self.assertIn("Returns:", code)
            self.assertIn("List of result rows", code)

        finally:
            os.remove(fname)
            os.remove(schema_fname)

    def test_method_body_generation(self):
        # Test that the template correctly generates method bodies for different SQL types
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users DEFAULT VALUES;
        """
        schema = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
        """

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        schema_fname = Path(fname).with_suffix(".schema")
        with open(schema_fname, "w") as f:
            f.write(schema)

        try:
            code = self.generator.generate_class(fname, schema_file_path=schema_fname)

            # Test class method structure
            self.assertIn("@classmethod", code)
            self.assertIn("def get_user(", code)
            self.assertIn("def create_user(", code)

            # Test fetch statement body
            self.assertIn('sql = """', code)
            self.assertIn("params = {", code)
            self.assertIn('"user_id": user_id,', code)
            self.assertIn("result = connection.execute(text(sql), params)", code)
            self.assertIn("return rows", code)

            # Test execute statement body (no automatic commit)
            self.assertIn("result = connection.execute(text(sql))", code)
            self.assertIn("Executed non-select operation", code)
            self.assertIn("return result", code)

        finally:
            os.remove(fname)
            os.remove(schema_fname)

    def test_complex_sql_generation(self):
        # Test CTE with multiple parameters
        sql = """# TestClass
#get_user_stats
WITH user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM users u
LEFT JOIN user_orders uo ON u.id = uo.user_id
WHERE u.id = :user_id AND u.status = :status
        """
        
        with temp_sql_files(sql, create_complex_schema()) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            assert_generated_code_structure(code, "TestClass", ["get_user_stats"])
            assert_method_parameters(code, "get_user_stats", ["user_id", "status"])
            
            # Verify complex SQL is preserved
            self.assertIn("WITH user_orders AS", code)
            self.assertIn("LEFT JOIN user_orders", code)
            self.assertIn('"user_id": user_id', code)
            self.assertIn('"status": status', code)

    def test_generated_code_syntax_validation(self):
        # Test that generated code is valid Python syntax
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        
        with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            # Try to parse the generated code as Python
            ast.parse(code)

    def test_generate_class_with_various_statement_types(self):
        sql = """# TestClass
#get_users
SELECT * FROM users;

#create_user
INSERT INTO users (name) VALUES (:name);

#update_user
UPDATE users SET status = :status WHERE id = :user_id;

#delete_user
DELETE FROM users WHERE id = :user_id;

#show_tables
SHOW TABLES;

#describe_table
DESCRIBE users;

#with_cte
WITH cte AS (SELECT 1) SELECT * FROM cte;
        """
        
        with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            # Check that all methods are generated as class methods
            assert_generated_code_structure(code, "TestClass", 
                ["get_users", "create_user", "update_user", "delete_user", "show_tables", "describe_table", "with_cte"])
            
            # Check for named parameters
            self.assertIn("connection: Connection,", code)

            # Check return types
            self.assertIn("-> List[Row]", code)  # Fetch statements
            self.assertIn("-> Result", code)  # Execute statements

            # Validate syntax
            ast.parse(code)

    def test_generate_multiple_classes_with_output_dir(self):
        sql_files = [
            ("""# ClassA
#get_a
SELECT 1;
            """, create_dummy_schema("dummy1")),
            ("""# ClassB
#get_b
SELECT 2;
            """, create_dummy_schema("dummy2"))
        ]
        
        with temp_multiple_sql_files(sql_files) as file_paths:
            sql_file_paths = [sql_path for sql_path, _ in file_paths]
            
            output_dir = tempfile.mkdtemp()
            try:
                schema_file_paths = [schema_path for _, schema_path in file_paths]
                result = self.generator.generate_multiple_classes(
                    sql_file_paths,
                    output_dir=output_dir,
                    schema_file_path=schema_file_paths[0],
                )
                self.assertEqual(len(result), 2)
                self.assertIn("ClassA", result)
                self.assertIn("ClassB", result)

                # Check that files were created
                files = os.listdir(output_dir)
                self.assertEqual(len(files), 2)
                self.assertTrue(all(f.endswith(".py") for f in files))
            finally:
                shutil.rmtree(output_dir, ignore_errors=True)

    def test_class_methods_only_generation(self):
        """Test that only class methods are generated, no instance methods or constructors."""
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name) VALUES (:name);
        """

        with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)

            # Verify only class methods are generated
            assert_generated_code_structure(code, "TestClass", ["get_user", "create_user"])

            # Verify no instance methods or constructors
            self.assertNotIn("def __init__", code)
            self.assertNotIn("self.", code)
            self.assertNotIn("self._connection", code)

            # Verify named parameters are used
            self.assertIn("connection: Connection,", code)

            # Verify class logger is defined
            self.assertIn("logger = logging.getLogger", code)

    def test_template_based_generation(self):
        """Test that the Jinja2 template-based generation works correctly."""
        sql = """# TemplateTest
#simple_query
SELECT * FROM test WHERE id = :test_id;
        """

        schema = """CREATE TABLE test (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
        """

        with temp_sql_files(sql, schema) as (sql_file, schema_file):
            code = self.generator.generate_class(sql_file, schema_file_path=schema_file)

            # Verify template-generated structure
            assert_generated_code_structure(code, "TemplateTest", ["simple_query"])
            assert_method_parameters(code, "simple_query", ["test_id"])
            
            self.assertIn("Select operation: simple_query", code)
            self.assertIn("Statement type: fetch", code)
            self.assertIn('"test_id": test_id,', code)
            self.assertIn("return rows", code)

            # Verify imports are present
            self.assertIn("from typing import Optional, List, Dict, Any", code)
            self.assertIn("from sqlalchemy import text", code)
            self.assertIn("from sqlalchemy.engine import Connection, Result", code)
            self.assertIn("from sqlalchemy.engine.row import Row", code)


if __name__ == "__main__":
    unittest.main()
