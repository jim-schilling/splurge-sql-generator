import ast
import logging
import os
import tempfile
import unittest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.sql_parser import SqlParser


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
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            self.assertIn("class TestClass", code)
            self.assertIn("def get_user", code)
            self.assertIn("def create_user", code)
            self.assertIn("user_id", code)
            self.assertIn("name", code)
            self.assertIn("email", code)
        finally:
            os.remove(fname)

    def test_generate_class_output_file(self):
        sql = """# TestClass
#get_one
SELECT 1;
        """
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            sql_fname = f.name
        py_fd, py_fname = tempfile.mkstemp(suffix=".py")
        os.close(py_fd)
        try:
            code = self.generator.generate_class(sql_fname, output_file_path=py_fname)
            self.assertTrue(os.path.exists(py_fname))
            with open(py_fname, "r") as f:
                content = f.read()
                self.assertIn("class TestClass", content)
                self.assertIn("def get_one", content)
        finally:
            os.remove(sql_fname)
            os.remove(py_fname)

    def test_generate_multiple_classes(self):
        sql1 = """# ClassA
#get_a
SELECT 1;
        """
        sql2 = """# ClassB
#get_b
SELECT 2;
        """
        with (
            tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f1,
            tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f2,
        ):
            f1.write(sql1)
            f2.write(sql2)
            fname1 = f1.name
            fname2 = f2.name
        try:
            result = self.generator.generate_multiple_classes([fname1, fname2])
            self.assertEqual(len(result), 2)
            self.assertIn("ClassA", result)
            self.assertIn("ClassB", result)
        finally:
            os.remove(fname1)
            os.remove(fname2)

    def test_generate_class_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_class("nonexistent_file.sql")

    def test_method_signature_generation(self):
        # Test various parameter scenarios
        test_cases = [
            ([], ""),
            (["user_id"], "user_id: Any"),
            (["user_id", "status"], "user_id: Any, status: Any"),
            (["user_id", "user_id"], "user_id: Any"),  # Duplicate parameters
            (["user_id_123", "status"], "user_id_123: Any, status: Any"),
        ]

        for params, expected in test_cases:
            signature = self.generator._generate_method_signature(params)
            self.assertEqual(signature, expected)

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

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name

        try:
            code = self.generator.generate_class(fname)

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

    def test_method_body_generation(self):
        # Test that the template correctly generates method bodies for different SQL types
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users DEFAULT VALUES;
        """

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name

        try:
            code = self.generator.generate_class(fname)

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
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            self.assertIn("class TestClass", code)
            self.assertIn("@classmethod", code)
            self.assertIn("def get_user_stats(", code)
            self.assertIn("connection: Connection,", code)
            self.assertIn("user_id: int,", code)
            self.assertIn("status: str,", code)
            self.assertIn('"user_id": user_id', code)
            self.assertIn('"status": status', code)
            self.assertIn("WITH user_orders AS", code)
        finally:
            os.remove(fname)

    def test_generated_code_syntax_validation(self):
        # Test that generated code is valid Python syntax
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            # Try to parse the generated code as Python
            ast.parse(code)
        finally:
            os.remove(fname)

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
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            # Check that all methods are generated as class methods
            self.assertIn("class TestClass", code)
            self.assertIn("@classmethod", code)
            self.assertIn("def get_users(", code)
            self.assertIn("def create_user(", code)
            self.assertIn("def update_user(", code)
            self.assertIn("def delete_user(", code)
            self.assertIn("def show_tables(", code)
            self.assertIn("def describe_table(", code)
            self.assertIn("def with_cte(", code)

            # Check for named parameters
            self.assertIn("connection: Connection,", code)

            # Check return types
            self.assertIn("-> List[Row]", code)  # Fetch statements
            self.assertIn("-> Result", code)  # Execute statements

            # Validate syntax
            ast.parse(code)
        finally:
            os.remove(fname)

    def test_generate_multiple_classes_with_output_dir(self):
        sql1 = """# ClassA
#get_a
SELECT 1;
        """
        sql2 = """# ClassB
#get_b
SELECT 2;
        """
        with (
            tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f1,
            tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f2,
        ):
            f1.write(sql1)
            f2.write(sql2)
            fname1 = f1.name
            fname2 = f2.name

        output_dir = tempfile.mkdtemp()
        try:
            result = self.generator.generate_multiple_classes(
                [fname1, fname2],
                output_dir=output_dir,
            )
            self.assertEqual(len(result), 2)
            self.assertIn("ClassA", result)
            self.assertIn("ClassB", result)

            # Check that files were created
            files = os.listdir(output_dir)
            self.assertEqual(len(files), 2)
            self.assertTrue(all(f.endswith(".py") for f in files))
        finally:
            os.remove(fname1)
            os.remove(fname2)
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

    def test_class_methods_only_generation(self):
        """Test that only class methods are generated, no instance methods or constructors."""
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name) VALUES (:name);
        """

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name

        try:
            code = self.generator.generate_class(fname)

            # Verify only class methods are generated
            self.assertIn("@classmethod", code)
            self.assertIn("def get_user(", code)
            self.assertIn("def create_user(", code)

            # Verify no instance methods or constructors
            self.assertNotIn("def __init__", code)
            self.assertNotIn("self.", code)
            self.assertNotIn("self._connection", code)

            # Verify named parameters are used
            self.assertIn("connection: Connection,", code)

            # Verify class logger is defined
            self.assertIn("logger = logging.getLogger", code)

        finally:
            os.remove(fname)

    def test_template_based_generation(self):
        """Test that the Jinja2 template-based generation works correctly."""
        sql = """# TemplateTest
#simple_query
SELECT * FROM test WHERE id = :test_id;
        """

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name

        try:
            code = self.generator.generate_class(fname)

            # Verify template-generated structure
            self.assertIn("class TemplateTest:", code)
            self.assertIn("@classmethod", code)
            self.assertIn("def simple_query(", code)
            self.assertIn("connection: Connection,", code)
            self.assertIn("test_id: int,", code)
            self.assertIn("Select operation: simple_query", code)
            self.assertIn("Statement type: fetch", code)
            self.assertIn('"test_id": test_id,', code)
            self.assertIn("return rows", code)

            # Verify imports are present
            self.assertIn("from typing import Optional, List, Dict, Any", code)
            self.assertIn("from sqlalchemy import text", code)
            self.assertIn("from sqlalchemy.engine import Connection, Result", code)
            self.assertIn("from sqlalchemy.engine.row import Row", code)

        finally:
            os.remove(fname)


if __name__ == "__main__":
    unittest.main()
