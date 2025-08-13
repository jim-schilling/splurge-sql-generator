#!/usr/bin/env python3
"""
Simple test script demonstrating the easy-to-use statement detection functions.
"""

from splurge_sql_generator import (
    detect_statement_type,
    is_execute_statement,
    is_fetch_statement,
)


def test_simple_statements():
    """Test simple SQL statements."""

    print("Testing Simple SQL Statements")
    print("=" * 40)

    test_cases = [
        ("SELECT * FROM users", "Simple SELECT"),
        ("INSERT INTO users (name) VALUES ('John')", "Simple INSERT"),
        ("UPDATE users SET active = 1", "Simple UPDATE"),
        ("DELETE FROM users WHERE id = 1", "Simple DELETE"),
        ("VALUES (1, 'John'), (2, 'Jane')", "VALUES statement"),
        ("SHOW TABLES", "SHOW statement"),
        ("EXPLAIN SELECT * FROM users", "EXPLAIN statement"),
        ("DESCRIBE users", "DESCRIBE statement"),
    ]

    for sql, description in test_cases:
        is_fetch = is_fetch_statement(sql)
        is_execute = is_execute_statement(sql)
        statement_type = detect_statement_type(sql)

        print(f"{description}:")
        print(f"  SQL: {sql}")
        print(f"  Type: {statement_type}")
        print(f"  Is Fetch: {is_fetch}")
        print(f"  Is Execute: {is_execute}")
        print()


def test_complex_statements():
    """Test complex SQL statements including CTEs."""

    print("Testing Complex SQL Statements")
    print("=" * 40)

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
            "CTE with SELECT",
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
            "CTE with INSERT",
        ),
        ("SELECT * FROM (SELECT id, name FROM users) AS u", "Subquery in FROM"),
        (
            "INSERT INTO users (name) VALUES (:name) RETURNING id",
            "INSERT with RETURNING",
        ),
    ]

    for sql, description in complex_cases:
        is_fetch = is_fetch_statement(sql)
        is_execute = is_execute_statement(sql)
        statement_type = detect_statement_type(sql)

        print(f"{description}:")
        print(f"  Type: {statement_type}")
        print(f"  Is Fetch: {is_fetch}")
        print(f"  Is Execute: {is_execute}")
        print()


def test_edge_cases():
    """Test edge cases and error handling."""

    print("Testing Edge Cases")
    print("=" * 40)

    edge_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("-- This is a comment", "Comment only"),
        ("/* Multi-line comment */", "Multi-line comment only"),
        ("SELECT * FROM users -- get all users", "SQL with comment"),
    ]

    for sql, description in edge_cases:
        is_fetch = is_fetch_statement(sql)
        is_execute = is_execute_statement(sql)
        statement_type = detect_statement_type(sql)

        print(f"{description}:")
        print(f"  Type: {statement_type}")
        print(f"  Is Fetch: {is_fetch}")
        print(f"  Is Execute: {is_execute}")
        print()


if __name__ == "__main__":
    print("SQL Statement Detection Test")
    print("=" * 50)
    print()

    test_simple_statements()
    print()

    test_complex_statements()
    print()

    test_edge_cases()

    print("=" * 50)
    print("All tests completed!")
