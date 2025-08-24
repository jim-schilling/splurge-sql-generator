"""
CLI integration tests for splurge-sql-generator.

These tests focus on CLI integration with real file operations.
"""

import shutil
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest

from splurge_sql_generator.cli import main as cli_main
from test_utils import (
    temp_sql_files,
    create_basic_schema
)


class TestCLIIntegration:
    """Test CLI integration with real file operations."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        self.temp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_with_real_files(self) -> None:
        """Test CLI with actual file operations."""
        sql_content = """# TestRepository
# get_data
SELECT * FROM test_table WHERE id = :id;
"""
        
        with temp_sql_files(sql_content, create_basic_schema("test_table")) as (sql_file, _):
            # Test dry run
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                # Simulate CLI call
                sys.argv = ['cli.py', sql_file, '--dry-run']
                cli_main()
                
                output = sys.stdout.getvalue()
                assert "class TestRepository:" in output
                assert "def get_data(" in output
            finally:
                sys.stdout = old_stdout

    def test_cli_output_generation(self) -> None:
        """Test CLI file output generation."""
        sql_content = """# UserService
# get_user
SELECT * FROM users WHERE id = :user_id;
"""
        
        with temp_sql_files(sql_content, create_basic_schema()) as (sql_file, _):
            output_dir = Path(self.temp_dir) / "output"
            
            # Test CLI with output directory
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                sys.argv = ['cli.py', sql_file, '-o', str(output_dir)]
                cli_main()
                
                # Validate output
                expected_file = output_dir / "user_service.py"
                assert expected_file.exists()
                
                content = expected_file.read_text()
                assert "class UserService:" in content
                assert "def get_user(" in content
            finally:
                sys.stdout = old_stdout
