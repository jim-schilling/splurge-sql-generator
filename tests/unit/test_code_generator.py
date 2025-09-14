import ast
import os
import shutil
import tempfile
from pathlib import Path
from tests.unit.test_utils import (
    temp_sql_files,
    temp_multiple_sql_files,
    create_basic_schema,
    create_dummy_schema,
    create_complex_schema,
    assert_generated_code_structure,
    assert_method_parameters,
)

import pytest


from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.sql_parser import SqlParser


@pytest.fixture
def generator():
    return PythonCodeGenerator()


@pytest.fixture
def parser():
    return SqlParser()


def test_generate_class_and_methods(generator, parser):
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """

    with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
        code = generator.generate_class(sql_file, schema_file_path=schema_file)
        assert_generated_code_structure(code, "TestClass", ["get_user", "create_user"])
        assert_method_parameters(code, "get_user", ["user_id"])
        assert_method_parameters(code, "create_user", ["name", "email"])


def test_generate_class_output_file(generator, parser):
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
    schema_fname = Path(sql_fname).with_suffix(".schema")
    with open(schema_fname, "w") as f:
        f.write(schema)
    py_fd, py_fname = tempfile.mkstemp(suffix=".py")
    os.close(py_fd)
    try:
        generator.generate_class(
            sql_fname, output_file_path=py_fname, schema_file_path=schema_fname
        )
        assert os.path.exists(py_fname)
        with open(py_fname, "r") as f:
            content = f.read()
            assert "class TestClass" in content
            assert "def get_one" in content
    finally:
        os.remove(sql_fname)
        os.remove(schema_fname)
        os.remove(py_fname)


def test_generate_multiple_classes(generator, parser):
    sql_files = [
        (
            """# ClassA
#get_a
SELECT 1;
            """,
            create_dummy_schema("dummy1"),
        ),
        (
            """# ClassB
#get_b
SELECT 2;
            """,
            create_dummy_schema("dummy2"),
        ),
    ]

    with temp_multiple_sql_files(sql_files) as file_paths:
        sql_file_paths = [sql_path for sql_path, _ in file_paths]
        schema_file_paths = [schema_path for _, schema_path in file_paths]
        # Use the first schema file as the shared schema
        result = generator.generate_multiple_classes(
            sql_file_paths, schema_file_path=schema_file_paths[0]
        )

        assert len(result) == 2
        assert "ClassA" in result
        assert "ClassB" in result
        assert_generated_code_structure(result["ClassA"], "ClassA", ["get_a"])
        assert_generated_code_structure(result["ClassB"], "ClassB", ["get_b"])


def test_generate_class_invalid_file(generator, parser):
    with pytest.raises(FileNotFoundError):
        generator.generate_class(
            "nonexistent_file.sql", schema_file_path="nonexistent.schema"
        )


def test_method_docstring_generation(generator, parser):
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
        code = generator.generate_class(fname, schema_file_path=schema_fname)

        # Test method with parameters
        assert "Select operation: get_user" in code
        assert "Statement type: fetch" in code
        assert "Args:" in code
        assert "connection: SQLAlchemy database connection" in code
        assert "user_id: Parameter for user_id" in code
        assert "List of result rows" in code

        # Test method with multiple parameters
        assert "Insert operation: create_user" in code
        assert "Statement type: execute" in code
        assert "name: Parameter for name" in code
        assert "email: Parameter for email" in code
        assert "SQLAlchemy Result object" in code

        # Test method with no SQL parameters (only connection)
        assert "Select operation: get_all" in code
        assert "Statement type: fetch" in code
        assert "Args:" in code
        assert "connection: SQLAlchemy database connection" in code
        assert "Returns:" in code
        assert "List of result rows" in code

    finally:
        os.remove(fname)
        os.remove(schema_fname)


def test_method_body_generation(generator, parser):
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
        code = generator.generate_class(fname, schema_file_path=schema_fname)

        # Test class method structure
        assert "@classmethod" in code
        assert "def get_user(" in code
        assert "def create_user(" in code

        # Test fetch statement body
        assert 'sql = """' in code
        assert "params = {" in code
        assert '"user_id": user_id,' in code
        assert "result = connection.execute(text(sql), params)" in code
        assert "return rows" in code

        # Test execute statement body (no automatic commit)
        assert "result = connection.execute(text(sql))" in code
        assert "Executed non-select operation" in code
        assert "return result" in code

    finally:
        os.remove(fname)
        os.remove(schema_fname)


def test_complex_sql_generation(generator, parser):
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
        code = generator.generate_class(sql_file, schema_file_path=schema_file)
        assert_generated_code_structure(code, "TestClass", ["get_user_stats"])
        assert_method_parameters(code, "get_user_stats", ["user_id", "status"])

        # Verify complex SQL is preserved
        assert "WITH user_orders AS" in code
        assert "LEFT JOIN user_orders" in code
        assert '"user_id": user_id' in code
        assert '"status": status' in code


def test_generated_code_syntax_validation(generator, parser):
    # Test that generated code is valid Python syntax
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """

    with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
        code = generator.generate_class(sql_file, schema_file_path=schema_file)
        # Try to parse the generated code as Python
        ast.parse(code)


def test_generate_class_with_various_statement_types(generator, parser):
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
        code = generator.generate_class(sql_file, schema_file_path=schema_file)
        # Check that all methods are generated as class methods
        assert_generated_code_structure(
            code,
            "TestClass",
            [
                "get_users",
                "create_user",
                "update_user",
                "delete_user",
                "show_tables",
                "describe_table",
                "with_cte",
            ],
        )

        # Check for named parameters
        assert "connection: Connection," in code

        # Check return types
        assert "-> List[Row]" in code  # Fetch statements
        assert "-> Result" in code  # Execute statements

        # Validate syntax
        ast.parse(code)


def test_generate_multiple_classes_with_output_dir(generator, parser):
    sql_files = [
        (
            """# ClassA
#get_a
SELECT 1;
            """,
            create_dummy_schema("dummy1"),
        ),
        (
            """# ClassB
#get_b
SELECT 2;
            """,
            create_dummy_schema("dummy2"),
        ),
    ]

    with temp_multiple_sql_files(sql_files) as file_paths:
        sql_file_paths = [sql_path for sql_path, _ in file_paths]

        output_dir = tempfile.mkdtemp()
        try:
            schema_file_paths = [schema_path for _, schema_path in file_paths]
            result = generator.generate_multiple_classes(
                sql_file_paths,
                output_dir=output_dir,
                schema_file_path=schema_file_paths[0],
            )
            assert len(result) == 2
            assert "ClassA" in result
            assert "ClassB" in result

            # Check that files were created
            files = os.listdir(output_dir)
            assert len(files) == 2
            assert all(f.endswith(".py") for f in files)
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


def test_class_methods_only_generation(generator, parser):
    """Test that only class methods are generated, no instance methods or constructors."""
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name) VALUES (:name);
        """

    with temp_sql_files(sql, create_basic_schema()) as (sql_file, schema_file):
        code = generator.generate_class(sql_file, schema_file_path=schema_file)

        # Verify only class methods are generated
        assert_generated_code_structure(code, "TestClass", ["get_user", "create_user"])

        # Verify no instance methods or constructors
        assert "def __init__" not in code
        assert "self." not in code
        assert "self._connection" not in code

        # Verify named parameters are used
        assert "connection: Connection," in code

        # Verify class logger is defined
        assert "logger = logging.getLogger" in code


def test_template_based_generation(generator, parser):
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
        code = generator.generate_class(sql_file, schema_file_path=schema_file)

        # Verify template-generated structure
        assert_generated_code_structure(code, "TemplateTest", ["simple_query"])
        assert_method_parameters(code, "simple_query", ["test_id"])

        assert "Select operation: simple_query" in code
        assert "Statement type: fetch" in code
        assert '"test_id": test_id,' in code
        assert "return rows" in code

        # Verify imports are present
        assert "from typing import Optional, List, Dict, Any" in code
        assert "from sqlalchemy import text" in code
        assert "from sqlalchemy.engine import Connection, Result" in code
        assert "from sqlalchemy.engine.row import Row" in code
