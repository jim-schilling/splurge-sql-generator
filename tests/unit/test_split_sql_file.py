"""
Unit tests for SQL file splitting functionality.

Tests the split_sql_file function from the sql_helper module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from splurge_sql_generator.sql_helper import split_sql_file
from splurge_sql_generator.errors import SqlFileError, SqlValidationError


class TestSplitSqlFile:
    """Test SQL file splitting functionality."""

    @pytest.fixture
    def temp_sql_file(self):
        """Create a temporary SQL file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("""
            -- Create users table
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            
            -- Insert sample data
            INSERT INTO users (name) VALUES ('Alice'), ('Bob');
            
            -- Query users
            SELECT * FROM users;
            """)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass

    def test_split_sql_file_success(self, temp_sql_file):
        """Test successful SQL file splitting."""
        result = split_sql_file(temp_sql_file)
        assert len(result) == 3
        assert "CREATE TABLE users" in result[0]
        assert "INSERT INTO users" in result[1]
        assert "SELECT * FROM users" in result[2]

    def test_split_sql_file_with_strip_semicolon(self, temp_sql_file):
        """Test SQL file splitting with strip_semicolon=True."""
        result = split_sql_file(temp_sql_file, strip_semicolon=True)
        assert len(result) == 3
        assert result[0].endswith(")")
        assert result[1].endswith("('Bob')")
        assert result[2].endswith("users")

    def test_split_sql_file_without_strip_semicolon(self, temp_sql_file):
        """Test SQL file splitting with strip_semicolon=False."""
        result = split_sql_file(temp_sql_file, strip_semicolon=False)
        assert len(result) == 3
        assert result[0].endswith(");")
        assert result[1].endswith("('Bob');")
        assert result[2].endswith("users;")

    def test_split_sql_file_with_pathlib_path(self, temp_sql_file):
        """Test SQL file splitting with pathlib.Path object."""
        path_obj = Path(temp_sql_file)
        result = split_sql_file(path_obj)
        assert len(result) == 3
        assert "CREATE TABLE users" in result[0]

    def test_split_sql_file_nonexistent(self):
        """Test splitting non-existent SQL file."""
        with pytest.raises(SqlFileError, match="SQL file not found"):
            split_sql_file("nonexistent.sql")

    def test_split_sql_file_none_path(self):
        """Test splitting with None file path."""
        with pytest.raises(SqlValidationError, match="file_path cannot be None"):
            split_sql_file(None)

    def test_split_sql_file_empty_path(self):
        """Test splitting with empty file path."""
        with pytest.raises(SqlValidationError, match="file_path cannot be empty"):
            split_sql_file("")

    def test_split_sql_file_invalid_type(self):
        """Test splitting with invalid file path type."""
        with pytest.raises(SqlValidationError, match="file_path must be a string or Path object"):
            split_sql_file(123)

    def test_split_sql_file_empty_content(self):
        """Test splitting SQL file with empty content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            result = split_sql_file(temp_file)
            assert result == []
        finally:
            os.unlink(temp_file)

    def test_split_sql_file_comments_only(self):
        """Test splitting SQL file with only comments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("""
            -- This is a comment
            /* This is a multi-line comment
               that spans multiple lines */
            """)
            temp_file = f.name
        
        try:
            result = split_sql_file(temp_file)
            assert result == []
        finally:
            os.unlink(temp_file)

    def test_split_sql_file_whitespace_only(self):
        """Test splitting SQL file with only whitespace."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("   \n\t  \n  ")
            temp_file = f.name
        
        try:
            result = split_sql_file(temp_file)
            assert result == []
        finally:
            os.unlink(temp_file)

    def test_split_sql_file_complex_statements(self):
        """Test splitting SQL file with complex statements."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("""
            -- Complex SQL file with various statement types
            
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_users_email ON users(email);
            
            INSERT INTO users (name, email) VALUES 
                ('Alice', 'alice@example.com'),
                ('Bob', 'bob@example.com'),
                ('Charlie', 'charlie@example.com');
            
            CREATE VIEW active_users AS
                SELECT id, name, email 
                FROM users 
                WHERE created_at > '2024-01-01';
            
            SELECT u.name, u.email, COUNT(p.id) as post_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id
            GROUP BY u.id, u.name, u.email
            HAVING COUNT(p.id) > 0;
            """)
            temp_file = f.name
        
        try:
            result = split_sql_file(temp_file)
            assert len(result) == 5
            assert "CREATE TABLE users" in result[0]
            assert "CREATE INDEX" in result[1]
            assert "INSERT INTO users" in result[2]
            assert "CREATE VIEW" in result[3]
            assert "SELECT u.name" in result[4]
        finally:
            os.unlink(temp_file)

    def test_split_sql_file_with_string_literals(self):
        """Test splitting SQL file with string literals containing special characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("""
            INSERT INTO messages (content) VALUES 
                ('Hello; this is a message with semicolon'),
                ('Another message with /* comment-like */ text'),
                ('Message with -- comment-like text');
            
            SELECT * FROM messages WHERE content LIKE '%;%';
            """)
            temp_file = f.name
        
        try:
            result = split_sql_file(temp_file)
            assert len(result) == 2
            assert "INSERT INTO messages" in result[0]
            assert "SELECT * FROM messages" in result[1]
        finally:
            os.unlink(temp_file)
