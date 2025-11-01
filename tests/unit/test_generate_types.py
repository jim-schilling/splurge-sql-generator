"""
Tests for generate_types_file functionality.

This module tests the generate_types_file feature that creates default SQL type mapping files.
"""

import os
import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator import generate_types_file
from splurge_sql_generator.schema_parser import SchemaParser


def test_generate_types_file_default_path():
    """Test generating types file with default path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Generate types file
            output_path = generate_types_file()

            # Check that file was created
            assert output_path == "types.yaml"
            assert Path("types.yaml").exists()

            # Check file content
            content = Path("types.yaml").read_text()
            assert "# SQL Type to Python Type Mapping" in content
            assert "INTEGER: int" in content
            assert "TEXT: str" in content
            assert "DEFAULT: Any" in content

        finally:
            # Restore original directory
            os.chdir(original_cwd)


def test_generate_types_file_custom_path():
    """Test generating types file with custom path."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        # Generate types file
        output_path = generate_types_file(output_path=temp_path)

        # Check that file was created
        assert output_path == temp_path
        assert Path(temp_path).exists()

        # Check file content
        content = Path(temp_path).read_text()
        assert "# SQL Type to Python Type Mapping" in content
        assert "INTEGER: int" in content
        assert "TEXT: str" in content
        assert "DEFAULT: Any" in content

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_generate_types_file_with_schema_parser():
    """Test generating types file using SchemaParser directly."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        # Generate types file using SchemaParser
        schema_parser = SchemaParser()
        output_path = schema_parser.generate_types_file(output_path=temp_path)

        # Check that file was created
        assert output_path == temp_path
        assert Path(temp_path).exists()

        # Check file content
        content = Path(temp_path).read_text()
        assert "# SQL Type to Python Type Mapping" in content
        assert "INTEGER: int" in content
        assert "TEXT: str" in content
        assert "DEFAULT: Any" in content

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_generate_types_file_content_structure():
    """Test that generated types file has correct structure."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        # Generate types file
        generate_types_file(output_path=temp_path)

        # Read content
        content = Path(temp_path).read_text()

        # Check header
        assert "# SQL Type to Python Type Mapping" in content
        assert "# This file maps SQL column types to Python type annotations" in content
        assert "# Customize this file for your specific database and requirements" in content

        # Check database sections
        assert "# SQLite types" in content
        assert "# PostgreSQL types" in content
        assert "# MySQL types" in content
        assert "# MSSQL types" in content
        assert "# Oracle types" in content

        # Check specific type mappings
        assert "INTEGER: int" in content
        assert "TEXT: str" in content
        assert "VARCHAR: str" in content
        assert "BOOLEAN: bool" in content
        assert "TIMESTAMP: str" in content
        assert "JSON: dict" in content
        assert "UUID: str" in content

        # Check default fallback
        assert "# Default fallback for unknown types" in content
        assert "DEFAULT: Any" in content

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_generate_types_file_directory_creation():
    """Test that generate_types_file creates directories if needed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a subdirectory path that doesn't exist
        sub_dir = Path(temp_dir) / "subdir" / "nested"
        output_path = sub_dir / "types.yaml"

        # Generate types file
        result_path = generate_types_file(output_path=str(output_path))

        # Check that directory was created and file exists
        assert result_path == str(output_path)
        assert output_path.exists()
        assert sub_dir.exists()

        # Check file content
        content = output_path.read_text()
        assert "# SQL Type to Python Type Mapping" in content


def test_generate_types_file_error_handling():
    """Test error handling when file cannot be written."""
    from splurge_sql_generator.exceptions import SplurgeSqlGeneratorFileError

    # Try to write to a directory (which should fail)
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(SplurgeSqlGeneratorFileError):
            generate_types_file(output_path=temp_dir)
