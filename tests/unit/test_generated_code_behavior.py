"""
Generated code behavior tests for splurge-sql-generator.

These tests focus on testing the behavior of generated code with mocked database connections.
"""

import importlib.util
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from tests.unit.test_utils import (
    temp_sql_files,
    create_basic_schema
)


class TestGeneratedCodeBehavior:
    """Test the behavior of generated code with mocked database connections."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        self.generator = PythonCodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generated_method_calls_database(self) -> None:
        """Test that generated method calls database with correct parameters."""
        sql_content = """# UserRepo
# get_user
SELECT * FROM users WHERE id = :user_id AND status = :status;
"""
        
        schema_content = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL
);
"""
        
        # Generate and import code
        module = self._create_and_import_module(sql_content, schema_content)
        UserRepo = module.UserRepo
        
        # Create mock connection
        mock_connection = Mock()
        mock_result = Mock()
        mock_connection.execute.return_value = mock_result
        mock_result.fetchall.return_value = [{'id': 1, 'name': 'Test User'}]
        
        # Call generated method
        result = UserRepo.get_user(
            connection=mock_connection,
            user_id=1,
            status='active'
        )
        
        # Validate database was called
        mock_connection.execute.assert_called_once()
        
        # Validate SQL and parameters
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text  # First argument is the SQL text object
        params = call_args[0][1]  # Second argument is the parameters
        
        assert "SELECT * FROM users WHERE id = :user_id AND status = :status" in sql_text
        assert params == {'user_id': 1, 'status': 'active'}
        
        # Validate result
        assert result == [{'id': 1, 'name': 'Test User'}]

    def test_generated_insert_method(self) -> None:
        """Test that generated INSERT method works correctly."""
        sql_content = """# UserRepo
# create_user
INSERT INTO users (name, email) VALUES (:name, :email) RETURNING id;
"""
        
        # Generate and import code
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserRepo = module.UserRepo
        
        # Create mock connection
        mock_connection = Mock()
        mock_result = Mock()
        mock_connection.execute.return_value = mock_result
        
        # Call generated method
        UserRepo.create_user(
            connection=mock_connection,
            name='Test User',
            email='test@example.com'
        )
        
        # Validate database was called
        mock_connection.execute.assert_called_once()
        
        # Validate SQL and parameters
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        params = call_args[0][1]
        
        assert "INSERT INTO users (name, email) VALUES (:name, :email)" in sql_text
        assert params == {'name': 'Test User', 'email': 'test@example.com'}

    def test_generated_update_method(self) -> None:
        """Test that generated UPDATE method works correctly."""
        sql_content = """# UserRepo
# update_user_status
UPDATE users SET status = :new_status WHERE id = :user_id;
"""
        
        schema_content = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL
);
"""
        
        # Generate and import code
        module = self._create_and_import_module(sql_content, schema_content)
        UserRepo = module.UserRepo
        
        # Create mock connection
        mock_connection = Mock()
        mock_result = Mock()
        mock_connection.execute.return_value = mock_result
        
        # Call generated method
        UserRepo.update_user_status(
            connection=mock_connection,
            user_id=1,
            new_status='inactive'
        )
        
        # Validate database was called
        mock_connection.execute.assert_called_once()
        
        # Validate SQL and parameters
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        params = call_args[0][1]
        
        assert "UPDATE users SET status = :new_status WHERE id = :user_id" in sql_text
        assert params == {'user_id': 1, 'new_status': 'inactive'}

    def test_generated_delete_method(self) -> None:
        """Test that generated DELETE method works correctly."""
        sql_content = """# UserRepo
# delete_user
DELETE FROM users WHERE id = :user_id;
"""
        
        # Generate and import code
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserRepo = module.UserRepo
        
        # Create mock connection
        mock_connection = Mock()
        mock_result = Mock()
        mock_connection.execute.return_value = mock_result
        
        # Call generated method
        UserRepo.delete_user(
            connection=mock_connection,
            user_id=1
        )
        
        # Validate database was called
        mock_connection.execute.assert_called_once()
        
        # Validate SQL and parameters
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        params = call_args[0][1]
        
        assert "DELETE FROM users WHERE id = :user_id" in sql_text
        assert params == {'user_id': 1}

    def test_generated_method_with_complex_sql(self) -> None:
        """Test that generated method with complex SQL works correctly."""
        sql_content = """# OrderRepo
# get_user_orders
SELECT 
    o.id as order_id,
    o.order_date,
    u.name as user_name,
    COUNT(od.id) as item_count,
    SUM(od.price * od.quantity) as total_amount
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_details od ON o.id = od.order_id
WHERE o.user_id = :user_id
GROUP BY o.id, o.order_date, u.name
ORDER BY o.order_date DESC;
"""
        
        schema_content = """CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    order_date DATE
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE order_details (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    price DECIMAL(10,2),
    quantity INTEGER
);
"""
        
        # Generate and import code
        module = self._create_and_import_module(sql_content, schema_content)
        OrderRepo = module.OrderRepo
        
        # Create mock connection
        mock_connection = Mock()
        mock_result = Mock()
        mock_connection.execute.return_value = mock_result
        mock_result.fetchall.return_value = [
            {'order_id': 1, 'order_date': '2023-01-01', 'user_name': 'Test User', 'item_count': 2, 'total_amount': 100.00}
        ]
        
        # Call generated method
        OrderRepo.get_user_orders(
            connection=mock_connection,
            user_id=1
        )
        
        # Validate database was called
        mock_connection.execute.assert_called_once()
        
        # Validate SQL contains complex query
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        
        assert "SELECT" in sql_text
        assert "JOIN users u ON o.user_id = u.id" in sql_text
        assert "LEFT JOIN order_details od ON o.id = od.order_id" in sql_text
        assert "GROUP BY o.id, o.order_date, u.name" in sql_text
        assert "ORDER BY o.order_date DESC" in sql_text

    def _create_and_import_module(self, sql_content: str, schema_content: str | None = None) -> Any:
        """Create SQL file, generate Python code, and import the generated module."""
        with temp_sql_files(sql_content, schema_content) as (sql_file, schema_file):
            # Generate Python code
            generated_code = self.generator.generate_class(sql_file, schema_file_path=schema_file)
            
            # Write generated code to file
            py_file = Path(self.temp_dir) / "generated_module.py"
            py_file.write_text(generated_code)
            
            # Import the generated module
            spec = importlib.util.spec_from_file_location("generated_module", py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
