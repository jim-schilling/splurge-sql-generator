"""
Template rendering tests for splurge-sql-generator.

These tests focus on Jinja2 template rendering with real data.
"""

import ast
import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from test_utils import (
    temp_sql_files,
    assert_generated_code_structure,
    assert_method_parameters
)


class TestTemplateRendering:
    """Test Jinja2 template rendering with real data."""

    def test_template_with_complex_data(self) -> None:
        """Test template rendering with complex method data."""
        generator = PythonCodeGenerator()
        
        # Create complex SQL with multiple methods
        sql_content = """# ComplexService
# get_users_by_status
SELECT id, username, email, status 
FROM users 
WHERE status = :status 
ORDER BY created_at DESC;

# create_user_with_profile
INSERT INTO users (username, email, password_hash) 
VALUES (:username, :email, :password_hash) 
RETURNING id;

# update_user_batch
UPDATE users 
SET status = :new_status, 
    updated_at = CURRENT_TIMESTAMP 
WHERE id IN (:user_ids);
"""
        
        schema_content = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
        
        with temp_sql_files(sql_content, schema_content) as (sql_file, _):
            # Generate code
            generated_code = generator.generate_class(sql_file)
            
            # Validate template rendering
            assert_generated_code_structure(generated_code, "ComplexService", 
                                          ["get_users_by_status", "create_user_with_profile", "update_user_batch"])
            
            # Validate method parameters
            assert_method_parameters(generated_code, "get_users_by_status", ["status"])
            assert_method_parameters(generated_code, "create_user_with_profile", 
                                   ["username", "email", "password_hash"])
            assert_method_parameters(generated_code, "update_user_batch", ["new_status", "user_ids"])
            
            # Validate SQL formatting
            assert "ORDER BY created_at DESC" in generated_code
            assert "WHERE id IN (:user_ids)" in generated_code
            
            # Validate Python syntax
            try:
                ast.parse(generated_code)
            except SyntaxError as e:
                pytest.fail(f"Generated code has syntax error: {e}")
