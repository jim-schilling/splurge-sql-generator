"""
Tests for parameter validation functionality.

This module tests the parameter validation feature that ensures SQL parameters
map to existing table/column combinations in the loaded schema.
"""

import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from splurge_sql_generator.exceptions import SqlValidationError


@pytest.fixture
def generator():
    return PythonCodeGenerator(validate_parameters=True)


def test_valid_parameters_pass_validation(generator):
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
        code = generator.generate_class(sql_fname, schema_file_path=schema_fname)
        assert "class TestClass" in code
        assert "def get_user" in code
        assert "def create_user" in code
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_invalid_parameters_raise_error(generator):
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
        with pytest.raises(SqlValidationError) as cm:
            generator.generate_class(sql_fname, schema_file_path=schema_fname)

        error_msg = str(cm.value)
        assert "user_id" in error_msg
        assert "users" in error_msg
        assert "Available columns" in error_msg
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_multiple_invalid_parameters_raise_error(generator):
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
        with pytest.raises(SqlValidationError) as cm:
            generator.generate_class(sql_fname, schema_file_path=schema_fname)

        error_msg = str(cm.value)
        assert "status" in error_msg
        assert "Available columns" in error_msg
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_validation_disabled_by_default(generator):
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
        assert "class TestClass" in code
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_validation_with_multiple_tables(generator):
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
        code = generator.generate_class(sql_fname, schema_file_path=schema_fname)
        assert "class TestClass" in code
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_validation_with_nonexistent_table(generator):
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
        with pytest.raises(SqlValidationError) as cm:
            generator.generate_class(sql_fname, schema_file_path=schema_fname)

        error_msg = str(cm.value)
        assert "id" in error_msg
        assert "users" in error_msg
        assert "Available columns: none" in error_msg
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_validation_with_no_parameters(generator):
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
        code = generator.generate_class(sql_fname, schema_file_path=schema_fname)
        assert "class TestClass" in code
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()


def test_validation_with_no_tables_in_query(generator):
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
        code = generator.generate_class(sql_fname, schema_file_path=schema_fname)
        assert "class TestClass" in code
    finally:
        Path(sql_fname).unlink()
        Path(schema_fname).unlink()
