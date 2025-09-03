"""
Tests for generate_types_file functionality.

This module tests the generate_types_file feature that creates default SQL type mapping files.
"""

import os
import tempfile
import unittest
from pathlib import Path

from splurge_sql_generator.schema_parser import SchemaParser
from splurge_sql_generator import generate_types_file


class TestGenerateTypesFile(unittest.TestCase):
    """Test generate_types_file functionality."""

    def test_generate_types_file_default_path(self):
        """Test generating types file with default path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Generate types file
                output_path = generate_types_file()
                
                # Check that file was created
                self.assertEqual(output_path, "types.yaml")
                self.assertTrue(Path("types.yaml").exists())
                
                # Check file content
                content = Path("types.yaml").read_text()
                self.assertIn("# SQL Type to Python Type Mapping", content)
                self.assertIn("INTEGER: int", content)
                self.assertIn("TEXT: str", content)
                self.assertIn("DEFAULT: Any", content)
                
            finally:
                # Restore original directory
                os.chdir(original_cwd)

    def test_generate_types_file_custom_path(self):
        """Test generating types file with custom path."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            # Generate types file
            output_path = generate_types_file(output_path=temp_path)
            
            # Check that file was created
            self.assertEqual(output_path, temp_path)
            self.assertTrue(Path(temp_path).exists())
            
            # Check file content
            content = Path(temp_path).read_text()
            self.assertIn("# SQL Type to Python Type Mapping", content)
            self.assertIn("INTEGER: int", content)
            self.assertIn("TEXT: str", content)
            self.assertIn("DEFAULT: Any", content)
            
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_generate_types_file_with_schema_parser(self):
        """Test generating types file using SchemaParser directly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            # Generate types file using SchemaParser
            schema_parser = SchemaParser()
            output_path = schema_parser.generate_types_file(output_path=temp_path)
            
            # Check that file was created
            self.assertEqual(output_path, temp_path)
            self.assertTrue(Path(temp_path).exists())
            
            # Check file content
            content = Path(temp_path).read_text()
            self.assertIn("# SQL Type to Python Type Mapping", content)
            self.assertIn("INTEGER: int", content)
            self.assertIn("TEXT: str", content)
            self.assertIn("DEFAULT: Any", content)
            
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_generate_types_file_content_structure(self):
        """Test that generated types file has correct structure."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            # Generate types file
            generate_types_file(output_path=temp_path)
            
            # Read content
            content = Path(temp_path).read_text()
            
            # Check header
            self.assertIn("# SQL Type to Python Type Mapping", content)
            self.assertIn("# This file maps SQL column types to Python type annotations", content)
            self.assertIn("# Customize this file for your specific database and requirements", content)
            
            # Check database sections
            self.assertIn("# SQLite types", content)
            self.assertIn("# PostgreSQL types", content)
            self.assertIn("# MySQL types", content)
            self.assertIn("# MSSQL types", content)
            self.assertIn("# Oracle types", content)
            
            # Check specific type mappings
            self.assertIn("INTEGER: int", content)
            self.assertIn("TEXT: str", content)
            self.assertIn("VARCHAR: str", content)
            self.assertIn("BOOLEAN: bool", content)
            self.assertIn("TIMESTAMP: str", content)
            self.assertIn("JSON: dict", content)
            self.assertIn("UUID: str", content)
            
            # Check default fallback
            self.assertIn("# Default fallback for unknown types", content)
            self.assertIn("DEFAULT: Any", content)
            
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_generate_types_file_directory_creation(self):
        """Test that generate_types_file creates directories if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subdirectory path that doesn't exist
            sub_dir = Path(temp_dir) / "subdir" / "nested"
            output_path = sub_dir / "types.yaml"
            
            # Generate types file
            result_path = generate_types_file(output_path=str(output_path))
            
            # Check that directory was created and file exists
            self.assertEqual(result_path, str(output_path))
            self.assertTrue(output_path.exists())
            self.assertTrue(sub_dir.exists())
            
            # Check file content
            content = output_path.read_text()
            self.assertIn("# SQL Type to Python Type Mapping", content)

    def test_generate_types_file_error_handling(self):
        """Test error handling when file cannot be written."""
        # Try to write to a directory (which should fail)
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(OSError):
                generate_types_file(output_path=temp_dir)


if __name__ == "__main__":
    unittest.main()
