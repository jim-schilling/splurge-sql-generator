"""
Unit tests for SQL statement detection functionality.

Tests the statement detection functions from the sql_helper module.
"""

import pytest

from splurge_sql_generator import (
    detect_statement_type,
    is_execute_statement,
    is_fetch_statement,
)
from splurge_sql_generator.sql_helper import EXECUTE_STATEMENT, FETCH_STATEMENT


class TestStatementDetection:
    """Test SQL statement detection functionality."""

    def test_simple_statements(self):
        """Test simple SQL statements."""
        test_cases = [
            ("SELECT * FROM users", FETCH_STATEMENT, True, False),
            ("INSERT INTO users (name) VALUES ('John')", EXECUTE_STATEMENT, False, True),
            ("UPDATE users SET active = 1", EXECUTE_STATEMENT, False, True),
            ("DELETE FROM users WHERE id = 1", EXECUTE_STATEMENT, False, True),
            ("VALUES (1, 'John'), (2, 'Jane')", FETCH_STATEMENT, True, False),
            ("SHOW TABLES", FETCH_STATEMENT, True, False),
            ("EXPLAIN SELECT * FROM users", FETCH_STATEMENT, True, False),
            ("DESCRIBE users", FETCH_STATEMENT, True, False),
        ]

        for sql, expected_type, expected_fetch, expected_execute in test_cases:
            assert detect_statement_type(sql) == expected_type
            assert is_fetch_statement(sql) == expected_fetch
            assert is_execute_statement(sql) == expected_execute


    def test_complex_statements(self):
        """Test complex SQL statements including CTEs."""
        complex_cases = [
            (
                """
            WITH user_stats AS (
                SELECT user_id, COUNT(*) as order_count
                FROM orders
                GROUP BY user_id
            )
            SELECT u.name, us.order_count
            FROM users u
            JOIN user_stats us ON u.id = us.user_id
            """,
                FETCH_STATEMENT,
                True,
                False,
            ),
            (
                """
            WITH user_data AS (
                SELECT id, name, email
                FROM temp_users
                WHERE valid = 1
            )
            INSERT INTO users (id, name, email)
            SELECT id, name, email FROM user_data
            """,
                EXECUTE_STATEMENT,
                False,
                True,
            ),
            ("SELECT * FROM (SELECT id, name FROM users) AS u", FETCH_STATEMENT, True, False),
            (
                "INSERT INTO users (name) VALUES (:name) RETURNING id",
                EXECUTE_STATEMENT,
                False,
                True,
            ),
        ]

        for sql, expected_type, expected_fetch, expected_execute in complex_cases:
            assert detect_statement_type(sql) == expected_type
            assert is_fetch_statement(sql) == expected_fetch
            assert is_execute_statement(sql) == expected_execute


    def test_edge_cases(self):
        """Test edge cases and error handling."""
        edge_cases = [
            ("", EXECUTE_STATEMENT, False, True),
            ("   ", EXECUTE_STATEMENT, False, True),
            ("-- This is a comment", EXECUTE_STATEMENT, False, True),
            ("/* Multi-line comment */", EXECUTE_STATEMENT, False, True),
            ("SELECT * FROM users -- get all users", FETCH_STATEMENT, True, False),
        ]

        for sql, expected_type, expected_fetch, expected_execute in edge_cases:
            assert detect_statement_type(sql) == expected_type
            assert is_fetch_statement(sql) == expected_fetch
            assert is_execute_statement(sql) == expected_execute
