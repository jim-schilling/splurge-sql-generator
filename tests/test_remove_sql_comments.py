"""
Unit tests for SQL comment removal functionality.

Tests the remove_sql_comments function from the sql_helper module.
"""

import pytest

from splurge_sql_generator.sql_helper import remove_sql_comments


class TestRemoveSqlComments:
    """Test SQL comment removal functionality."""

    def test_empty_string(self):
        """Test removing comments from empty string."""
        result = remove_sql_comments("")
        assert result == ""

    def test_none_string(self):
        """Test removing comments from None string."""
        result = remove_sql_comments(None)
        assert result is None

    def test_no_comments(self):
        """Test SQL with no comments."""
        sql = "SELECT * FROM users WHERE active = 1"
        result = remove_sql_comments(sql)
        assert result == "SELECT * FROM users WHERE active = 1"

    def test_single_line_comments(self):
        """Test removing single-line comments."""
        sql = """
        SELECT * FROM users -- This is a comment
        WHERE active = 1 -- Another comment
        """
        result = remove_sql_comments(sql)
        assert "--" not in result
        assert "SELECT * FROM users" in result
        assert "WHERE active = 1" in result

    def test_multi_line_comments(self):
        """Test removing multi-line comments."""
        sql = """
        SELECT * FROM users
        /* This is a multi-line comment
           that spans multiple lines */
        WHERE active = 1
        """
        result = remove_sql_comments(sql)
        assert "/*" not in result
        assert "*/" not in result
        assert "SELECT * FROM users" in result
        assert "WHERE active = 1" in result

    def test_comments_in_string_literals(self):
        """Test that comments within string literals are preserved."""
        sql = """
        SELECT * FROM users 
        WHERE name = 'John -- This is not a comment'
        AND description = '/* This is also not a comment */'
        """
        result = remove_sql_comments(sql)
        assert "'John -- This is not a comment'" in result
        assert "'/* This is also not a comment */'" in result

    def test_mixed_comments(self):
        """Test removing mixed single-line and multi-line comments."""
        sql = """
        -- Header comment
        SELECT * FROM users
        /* Multi-line comment
           with multiple lines */
        WHERE active = 1 -- Inline comment
        """
        result = remove_sql_comments(sql)
        assert "--" not in result
        assert "/*" not in result
        assert "*/" not in result
        assert "SELECT * FROM users" in result
        assert "WHERE active = 1" in result
