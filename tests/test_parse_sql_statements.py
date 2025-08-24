"""
Unit tests for SQL statement parsing functionality.

Tests the parse_sql_statements function from the sql_helper module.
"""

import pytest

from splurge_sql_generator.sql_helper import parse_sql_statements


class TestParseSqlStatements:
    """Test SQL statement parsing functionality."""

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_sql_statements("")
        assert result == []

    def test_none_string(self):
        """Test parsing None string."""
        result = parse_sql_statements(None)
        assert result == []

    def test_single_statement(self):
        """Test parsing single SQL statement."""
        sql = "SELECT * FROM users"
        result = parse_sql_statements(sql)
        assert len(result) == 1
        assert result[0] == "SELECT * FROM users"

    def test_multiple_statements(self):
        """Test parsing multiple SQL statements."""
        sql = "SELECT * FROM users; INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql)
        assert len(result) == 2
        assert "SELECT * FROM users" in result[0]
        assert "INSERT INTO users (name) VALUES ('John')" in result[1]

    def test_statements_with_comments(self):
        """Test parsing statements with comments."""
        sql = """
        -- First statement
        SELECT * FROM users;
        /* Second statement */
        INSERT INTO users (name) VALUES ('John');
        """
        result = parse_sql_statements(sql)
        assert len(result) == 2
        assert "SELECT * FROM users" in result[0]
        assert "INSERT INTO users (name) VALUES ('John')" in result[1]

    def test_empty_statements_filtered(self):
        """Test that empty statements are filtered out."""
        sql = "SELECT * FROM users;;;INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql)
        assert len(result) == 2
        assert "SELECT * FROM users" in result[0]
        assert "INSERT INTO users (name) VALUES ('John')" in result[1]

    def test_whitespace_only_statements_filtered(self):
        """Test that whitespace-only statements are filtered out."""
        sql = "SELECT * FROM users;   \n\t  ;INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql)
        assert len(result) == 2
        assert "SELECT * FROM users" in result[0]
        assert "INSERT INTO users (name) VALUES ('John')" in result[1]

    def test_comment_only_statements_filtered(self):
        """Test that comment-only statements are filtered out."""
        sql = "SELECT * FROM users; -- Comment only; INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql)
        assert len(result) == 1
        assert "SELECT * FROM users" in result[0]

    def test_strip_semicolon_true(self):
        """Test parsing with strip_semicolon=True."""
        sql = "SELECT * FROM users; INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql, strip_semicolon=True)
        assert len(result) == 2
        assert result[0] == "SELECT * FROM users"
        assert result[1] == "INSERT INTO users (name) VALUES ('John')"

    def test_strip_semicolon_false(self):
        """Test parsing with strip_semicolon=False."""
        sql = "SELECT * FROM users; INSERT INTO users (name) VALUES ('John');"
        result = parse_sql_statements(sql, strip_semicolon=False)
        assert len(result) == 2
        assert "SELECT * FROM users" in result[0]
        assert "INSERT INTO users (name) VALUES ('John')" in result[1]

    def test_complex_statements(self):
        """Test parsing complex SQL statements."""
        sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        );
        
        INSERT INTO users (name, email) VALUES 
            ('Alice', 'alice@example.com'),
            ('Bob', 'bob@example.com');
            
        SELECT * FROM users WHERE active = 1;
        """
        result = parse_sql_statements(sql)
        assert len(result) == 3
        assert "CREATE TABLE users" in result[0]
        assert "INSERT INTO users" in result[1]
        assert "SELECT * FROM users" in result[2]

    def test_statements_with_string_literals(self):
        """Test parsing statements with string literals containing semicolons."""
        sql = """
        INSERT INTO users (name, description) VALUES 
            ('John', 'User; with semicolon in description');
        SELECT * FROM users WHERE name = 'Alice; Bob';
        """
        result = parse_sql_statements(sql)
        assert len(result) == 2
        assert "INSERT INTO users" in result[0]
        assert "SELECT * FROM users" in result[1]
