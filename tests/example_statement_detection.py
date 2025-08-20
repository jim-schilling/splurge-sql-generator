#!/usr/bin/env python3
"""
Example script demonstrating how to use sql_helper methods to determine
if SQL statements are fetch or execute statements.

This script shows how to leverage the sophisticated SQL parsing capabilities
from sql_helper.py to accurately classify SQL statements.
"""

from splurge_sql_generator.sql_helper import (
    EXECUTE_STATEMENT,
    FETCH_STATEMENT,
    detect_statement_type,
)
from splurge_sql_generator.sql_parser import SqlParser


def demonstrate_statement_detection():
    """Demonstrate the statement detection functionality."""

    # Example SQL statements to test
    test_statements = [
        # Simple SELECT statements (fetch)
        "SELECT * FROM users",
        "SELECT id, name FROM users WHERE active = 1",
        # CTE statements (fetch)
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
        # VALUES statements (fetch)
        "VALUES (1, 'John'), (2, 'Jane')",
        # SHOW/EXPLAIN statements (fetch)
        "SHOW TABLES",
        "EXPLAIN SELECT * FROM users",
        "DESCRIBE users",
        # INSERT statements (execute)
        "INSERT INTO users (name, email) VALUES (:name, :email)",
        "INSERT INTO users SELECT * FROM temp_users",
        # UPDATE statements (execute)
        "UPDATE users SET active = 0 WHERE last_login < :cutoff_date",
        # DELETE statements (execute)
        "DELETE FROM users WHERE id = :user_id",
        # CREATE/ALTER/DROP statements (execute)
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
        "ALTER TABLE users ADD COLUMN email TEXT",
        "DROP TABLE temp_users",
        # Complex CTE with INSERT (execute)
        """
        WITH user_data AS (
            SELECT id, name, email
            FROM temp_users
            WHERE valid = 1
        )
        INSERT INTO users (id, name, email)
        SELECT id, name, email FROM user_data
        """,
    ]

    print("SQL Statement Type Detection Examples")
    print("=" * 50)
    print()

    for i, sql in enumerate(test_statements, 1):
        # Clean up the SQL for display
        clean_sql = sql.strip().replace("\n", " ").replace("  ", " ")
        if len(clean_sql) > 80:
            clean_sql = clean_sql[:77] + "..."

        # Detect statement type
        statement_type = detect_statement_type(sql)
        is_fetch = statement_type == FETCH_STATEMENT

        print(f"Example {i}:")
        print(f"  SQL: {clean_sql}")
        print(f"  Type: {statement_type}")
        print(f"  Is Fetch: {is_fetch}")
        print()


def demonstrate_parser_integration():
    """Demonstrate how the SQL parser uses the statement detection."""

    # Create a simple SQL template
    sql_template = """
#get_user_by_id
SELECT id, name, email FROM users WHERE id = :user_id

#create_user
INSERT INTO users (name, email) VALUES (:name, :email)

#update_user_status
UPDATE users SET active = :active WHERE id = :user_id

#delete_user
DELETE FROM users WHERE id = :user_id

#get_user_stats
WITH user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM users u
LEFT JOIN user_orders uo ON u.id = uo.user_id
WHERE u.id = :user_id
"""

    print("SQL Parser Integration Example")
    print("=" * 40)
    print()

    # Parse the template
    parser = SqlParser()

    # Simulate parsing by creating method queries manually
    method_queries = {
        "get_user_by_id": "SELECT id, name, email FROM users WHERE id = :user_id",
        "create_user": "INSERT INTO users (name, email) VALUES (:name, :email)",
        "update_user_status": "UPDATE users SET active = :active WHERE id = :user_id",
        "delete_user": "DELETE FROM users WHERE id = :user_id",
        "get_user_stats": """
        WITH user_orders AS (
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            GROUP BY user_id
        )
        SELECT u.name, uo.order_count
        FROM users u
        LEFT JOIN user_orders uo ON u.id = uo.user_id
        WHERE u.id = :user_id
        """,
    }

    for method_name, sql_query in method_queries.items():
        method_info = parser.get_method_info(sql_query)

        print(f"Method: {method_name}")
        print(f"  Query Type: {method_info['type']}")
        print(f"  Statement Type: {method_info['statement_type']}")
        print(f"  Is Fetch: {method_info['is_fetch']}")
        print(f"  Parameters: {method_info['parameters']}")
        print()


def demonstrate_edge_cases():
    """Demonstrate edge cases and complex SQL scenarios."""

    edge_cases = [
        # Empty or whitespace-only SQL
        ("", "Empty SQL"),
        ("   ", "Whitespace only"),
        # Comments only
        ("-- This is a comment", "Comment only"),
        ("/* Multi-line comment */", "Multi-line comment only"),
        # SQL with comments
        ("SELECT * FROM users -- get all users", "SQL with comment"),
        # Complex CTE with multiple statements
        (
            """
        WITH cte1 AS (SELECT 1 as id),
             cte2 AS (SELECT 2 as id)
        SELECT * FROM cte1 UNION SELECT * FROM cte2
        """,
            "Complex CTE with multiple CTEs",
        ),
        # INSERT with RETURNING (should be execute, not fetch)
        (
            "INSERT INTO users (name) VALUES (:name) RETURNING id",
            "INSERT with RETURNING",
        ),
        # Subquery in FROM clause
        ("SELECT * FROM (SELECT id, name FROM users) AS u", "Subquery in FROM"),
    ]

    print("Edge Cases and Complex Scenarios")
    print("=" * 40)
    print()

    for sql, description in edge_cases:
        statement_type = detect_statement_type(sql)
        is_fetch = statement_type == FETCH_STATEMENT

        print(f"Case: {description}")
        print(f"  Type: {statement_type}")
        print(f"  Is Fetch: {is_fetch}")
        print()


if __name__ == "__main__":
    print("SQL Statement Detection Examples")
    print("=" * 50)
    print()

    demonstrate_statement_detection()
    print("\n" + "=" * 50 + "\n")

    demonstrate_parser_integration()
    print("\n" + "=" * 50 + "\n")

    demonstrate_edge_cases()

    print("\n" + "=" * 50)
    print("All examples completed!")
