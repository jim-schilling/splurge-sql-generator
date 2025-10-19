"""
Generated code error handling tests for splurge-sql-generator.

These tests focus on error handling in generated code.
"""

import importlib.util
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from tests.unit.test_utils import create_basic_schema, temp_sql_files


class TestGeneratedCodeErrorHandling:
    """Test error handling in generated code."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        self.generator = PythonCodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generated_method_handles_database_errors(self) -> None:
        """Test that generated method properly handles database errors."""
        sql_content = """# UserRepo
# get_user
SELECT * FROM users WHERE id = :user_id;
"""

        # Generate and import code
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserRepo = module.UserRepo

        # Create mock connection that raises an exception
        mock_connection = Mock()
        mock_connection.execute.side_effect = Exception("Database connection failed")

        # Call generated method and expect exception to be re-raised
        with pytest.raises(Exception) as exc_info:
            UserRepo.get_user(connection=mock_connection, user_id=1)

        assert str(exc_info.value) == "Database connection failed"

    def test_generated_method_logs_errors(self) -> None:
        """Test that generated method logs errors appropriately."""
        sql_content = """# UserRepo
# get_user
SELECT * FROM users WHERE id = :user_id;
"""

        # Generate and import code
        module = self._create_and_import_module(sql_content, create_basic_schema())
        UserRepo = module.UserRepo

        # Create mock connection that raises an exception
        mock_connection = Mock()
        mock_connection.execute.side_effect = Exception("Database error")

        # Mock the logger
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr(UserRepo, "logger", mock_logger)
            try:
                UserRepo.get_user(connection=mock_connection, user_id=1)
            except Exception:
                pass  # Expected to fail

            # Validate error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "Error in get_user operation" in error_call

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
