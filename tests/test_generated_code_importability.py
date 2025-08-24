"""
Generated code importability tests for splurge-sql-generator.

These tests focus on validating that generated code can be imported and used.
"""

import importlib.util
import inspect
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from test_utils import (
    temp_sql_files,
    create_basic_schema
)


class TestGeneratedCodeImportability:
    """Test that generated code can be imported and used."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        self.generator = PythonCodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_and_import_module(self, sql_content: str, schema_content: str | None = None) -> Any:
        """
        Create SQL file, generate Python code, and import the generated module.
        
        Args:
            sql_content: SQL content to generate from
            schema_content: Optional schema content
            
        Returns:
            Imported module object
        """
        with temp_sql_files(sql_content, schema_content) as (sql_file, _):
            # Generate Python code
            generated_code = self.generator.generate_class(sql_file)
            
            # Write generated code to file
            py_file = Path(self.temp_dir) / "generated_module.py"
            py_file.write_text(generated_code)
            
            # Import the generated module
            spec = importlib.util.spec_from_file_location("generated_module", py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module

    def test_generated_class_can_be_imported(self) -> None:
        """Test that generated class can be imported without errors."""
        sql_content = """# TestRepository
# get_user
SELECT * FROM users WHERE id = :user_id;
"""
        
        module = self._create_and_import_module(sql_content, create_basic_schema())
        
        # Validate class exists
        assert hasattr(module, 'TestRepository')
        assert callable(module.TestRepository)
        
        # Validate class is a class
        assert isinstance(module.TestRepository, type)

    def test_generated_methods_exist(self) -> None:
        """Test that generated methods exist and are callable."""
        sql_content = """# UserService
# get_user_by_id
SELECT * FROM users WHERE id = :user_id;

# create_user
INSERT INTO users (name, email) VALUES (:name, :email);
"""
        
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserService = module.UserService
        
        # Validate methods exist
        assert hasattr(UserService, 'get_user_by_id')
        assert hasattr(UserService, 'create_user')
        
        # Validate methods are callable
        assert callable(UserService.get_user_by_id)
        assert callable(UserService.create_user)

    def test_generated_method_signatures(self) -> None:
        """Test that generated methods have correct signatures."""
        sql_content = """# TestRepo
# get_user
SELECT * FROM users WHERE id = :user_id AND status = :status;
"""
        
        schema_content = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL
);
"""
        
        module = self._create_and_import_module(sql_content, schema_content)
        TestRepo = module.TestRepo
        
        # Get method signature
        sig = inspect.signature(TestRepo.get_user)
        
        # Validate parameters
        params = list(sig.parameters.keys())
        assert 'connection' in params
        assert 'user_id' in params
        assert 'status' in params
        
        # Validate parameter types (all use Any)
        annotations = TestRepo.get_user.__annotations__
        assert annotations['user_id'] == Any
        assert annotations['status'] == Any

    def test_generated_code_follows_python_conventions(self) -> None:
        """Test that generated code follows Python conventions."""
        sql_content = """# UserRepository
# get_user_by_id
SELECT id, name, email FROM users WHERE id = :user_id;

# create_user
INSERT INTO users (name, email) VALUES (:name, :email) RETURNING id;
"""
        
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserRepository = module.UserRepository
        
        # Validate class name follows PascalCase
        assert UserRepository.__name__ == 'UserRepository'
        
        # Validate methods follow snake_case
        assert hasattr(UserRepository, 'get_user_by_id')
        assert hasattr(UserRepository, 'create_user')
        
        # Validate docstrings exist
        assert UserRepository.get_user_by_id.__doc__ is not None
        assert UserRepository.create_user.__doc__ is not None

    def test_generated_code_has_required_imports(self) -> None:
        """Test that generated code has all required imports."""
        sql_content = """# TestRepo
# get_data
SELECT * FROM test_table WHERE id = :id;
"""
        
        schema_content = """CREATE TABLE test_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""
        
        with temp_sql_files(sql_content, schema_content) as (sql_file, _):
            generated_code = self.generator.generate_class(sql_file)
            
            # Validate required imports
            required_imports = [
                'from sqlalchemy import text',
                'from sqlalchemy.engine import Connection, Result',
                'from sqlalchemy.engine.row import Row',
                'import logging',
                'from typing import Optional, List, Dict, Any'
            ]
            
            for import_stmt in required_imports:
                assert import_stmt in generated_code

    def test_generated_class_has_logger(self) -> None:
        """Test that generated class has a logger attribute."""
        sql_content = """# TestRepo
# get_data
SELECT * FROM test_table WHERE id = :id;
"""
        
        schema_content = """CREATE TABLE test_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""
        
        module = self._create_and_import_module(sql_content, schema_content)
        TestRepo = module.TestRepo
        
        # Validate logger exists
        assert hasattr(TestRepo, 'logger')
        assert TestRepo.logger is not None

    def test_generated_methods_are_class_methods(self) -> None:
        """Test that generated methods are class methods."""
        sql_content = """# TestRepo
# get_data
SELECT * FROM test_table WHERE id = :id;
"""
        
        schema_content = """CREATE TABLE test_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""
        
        module = self._create_and_import_module(sql_content, schema_content)
        TestRepo = module.TestRepo
        
        # Validate method is a class method
        assert inspect.ismethod(TestRepo.get_data)
        assert TestRepo.get_data.__self__ is TestRepo
