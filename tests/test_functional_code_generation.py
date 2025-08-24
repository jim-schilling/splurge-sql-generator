"""
Functional code generation tests for splurge-sql-generator.

These tests focus on complete code generation workflows with real files.
"""

import ast
import shutil
import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from test_utils import (
    temp_sql_files,
    temp_multiple_sql_files,
    create_basic_schema,
    create_dummy_schema,
    create_complex_schema,
    assert_generated_code_structure,
    assert_method_parameters
)


class TestFunctionalCodeGeneration:
    """Test complete code generation workflows with real files."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        self.generator = PythonCodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_user_repository_generation(self) -> None:
        """Test generating a complete User repository with schema."""
        sql_content = """# UserRepository
# get_user_by_id
SELECT id, username, email, created_at 
FROM users 
WHERE id = :user_id;

# create_user
INSERT INTO users (username, email, password_hash, status) 
VALUES (:username, :email, :password_hash, :status) 
RETURNING id;

# update_user_status
UPDATE users 
SET status = :new_status, updated_at = CURRENT_TIMESTAMP 
WHERE id = :user_id;
"""
        
        schema_content = """-- User.schema
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
        
        with temp_sql_files(sql_content, schema_content) as (sql_file, schema_file):
            generated_code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            
            # Validate generated code structure
            assert_generated_code_structure(generated_code, "UserRepository", 
                                          ["get_user_by_id", "create_user", "update_user_status"])
            
            # Validate method parameters
            assert_method_parameters(generated_code, "get_user_by_id", ["user_id"])
            assert_method_parameters(generated_code, "create_user", 
                                   ["username", "email", "password_hash", "status"])
            assert_method_parameters(generated_code, "update_user_status", ["new_status", "user_id"])
        
        # Validate SQL content
        assert "SELECT id, username, email, created_at" in generated_code
        assert "INSERT INTO users" in generated_code
        assert "UPDATE users" in generated_code
        
        # Validate Python syntax
        try:
            ast.parse(generated_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_multiple_classes_with_schemas(self) -> None:
        """Test generating multiple classes with different schemas."""
        # Create multiple SQL files with schemas
        files_data = [
            ("""# UserRepo
# get_user
SELECT * FROM users WHERE id = :user_id;
            """, create_basic_schema()),
            ("""# ProductRepo
# get_product
SELECT * FROM products WHERE id = :product_id;
            """, """CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price DECIMAL(10,2)
);
            """)
        ]
        
        with temp_multiple_sql_files(files_data) as file_paths:
            sql_file_paths = [sql_path for sql_path, _ in file_paths]
            schema_file_paths = [schema_path for _, schema_path in file_paths]
            result = self.generator.generate_multiple_classes(sql_file_paths, schema_file_path=schema_file_paths[0])
            
            # Validate results
            assert len(result) == 2
            assert "UserRepo" in result
            assert "ProductRepo" in result
            
            # Validate each generated class
            for class_name, code in result.items():
                assert f"class {class_name}:" in code
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    pytest.fail(f"Generated code for {class_name} has syntax error: {e}")

    def test_complex_sql_with_joins_and_subqueries(self) -> None:
        """Test generating code for complex SQL with joins and subqueries."""
        sql_content = """# OrderService
# get_user_orders_with_details
SELECT 
    o.id as order_id,
    o.order_date,
    u.username,
    p.name as product_name,
    od.quantity,
    od.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_details od ON o.id = od.order_id
JOIN products p ON od.product_id = p.id
WHERE o.user_id = :user_id
ORDER BY o.order_date DESC;

# get_order_summary
SELECT 
    user_id,
    COUNT(*) as order_count,
    SUM(total_amount) as total_spent
FROM orders 
WHERE order_date >= :start_date 
GROUP BY user_id
HAVING SUM(total_amount) > :min_amount;
"""
        
        with temp_sql_files(sql_content, create_complex_schema()) as (sql_file, schema_file):
            generated_code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            
            # Validate complex SQL handling
            assert_generated_code_structure(generated_code, "OrderService", 
                                          ["get_user_orders_with_details", "get_order_summary"])
            
            # Validate method parameters
            assert_method_parameters(generated_code, "get_user_orders_with_details", ["user_id"])
            assert_method_parameters(generated_code, "get_order_summary", ["start_date", "min_amount"])
            
            # Validate SQL content preservation
            assert "JOIN users u ON o.user_id = u.id" in generated_code
            assert "GROUP BY user_id" in generated_code
            assert "HAVING SUM(total_amount) > :min_amount" in generated_code

    def test_file_output_and_naming(self) -> None:
        """Test file output with proper naming conventions."""
        sql_content = """# UserRepository
# get_user
SELECT * FROM users WHERE id = :user_id;
"""
        
        with temp_sql_files(sql_content, create_basic_schema()) as (sql_file, schema_file):
            output_dir = Path(self.temp_dir) / "output"
            
            # Generate with output directory
            result = self.generator.generate_multiple_classes(
                [sql_file], 
                output_dir=str(output_dir),
                schema_file_path=schema_file
            )
            
            # Validate output directory creation
            assert output_dir.exists()
            
            # Validate filename conversion (PascalCase to snake_case)
            expected_file = output_dir / "user_repository.py"
            assert expected_file.exists()
            
            # Validate file content
            content = expected_file.read_text()
            assert "class UserRepository:" in content
            assert "def get_user(" in content

    def test_error_handling_with_invalid_files(self) -> None:
        """Test error handling with invalid or missing files."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            self.generator.generate_class("nonexistent_file.sql", schema_file_path="nonexistent.schema")
        
        # Test with valid SQL but missing schema (should fail now)
        valid_sql = """# TestClass
# test_method
SELECT * FROM test_table WHERE id = :id;
"""
        
        sql_file = Path(self.temp_dir) / "valid_no_schema.sql"
        sql_file.write_text(valid_sql)
        
        # Should fail without schema file (schema files are required)
        with pytest.raises(ValueError, match="No schema file provided"):
            self.generator.generate_class(str(sql_file), schema_file_path=None)

    def test_schema_required_validation(self) -> None:
        """Test that schema files are required for all SQL files."""
        sql_content = """# TestRepo
# test_method
SELECT * FROM test_table WHERE id = :id AND name = :name;
"""
        
        # Test with various column types
        schema_content = """CREATE TABLE test_table (
    id INTEGER PRIMARY KEY,
    name TEXT,
    amount DECIMAL(10,2),
    is_active BOOLEAN,
    created_date DATE,
    updated_time TIMESTAMP,
    json_data JSON,
    binary_data BLOB
);
"""
        
        with temp_sql_files(sql_content, schema_content) as (sql_file, schema_file):
            generated_code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            
            # Validate that all parameters use Any type (no type inference)
            assert "id: Any" in generated_code
            assert "name: Any" in generated_code
