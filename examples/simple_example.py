#!/usr/bin/env python3
"""
Simple Example for splurge-sql-generator

This example demonstrates the simplified logger approach with a working database setup.
"""

import logging
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

# Add the parent directory to the path to import from output
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the generated classes
from output.User import User


def setup_logging():
    """Configure logging to see the class-level logger in action."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_test_database():
    """Create a test database with the correct schema."""
    engine = create_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        # Create users table with all required columns
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Insert test data
        conn.execute(
            text(
                """
            INSERT INTO users (id, username, email, password_hash, status) VALUES 
            (1, 'john_doe', 'john@example.com', 'hashed_password_123', 'active'),
            (2, 'jane_smith', 'jane@example.com', 'hashed_password_456', 'active'),
            (3, 'bob_wilson', 'bob@example.com', 'hashed_password_789', 'inactive')
        """
            )
        )
        conn.commit()

    return engine


def demonstrate_simplified_logger():
    """Demonstrate the simplified logger approach."""
    print("=== Simplified Logger Demonstration ===")
    print()

    # Setup logging
    setup_logging()

    # Create database
    engine = create_test_database()

    with engine.connect() as connection:
        print("1. Fetching user by ID (notice the logger output above):")
        users = User.get_user_by_id(connection=connection, user_id=1)

        if users:
            user = users[0]
            print(f"   Found user: {user.username} ({user.email})")
        print()

        print("2. Fetching users by status:")
        active_users = User.get_users_by_status(connection=connection, status="active")
        print(f"   Found {len(active_users)} active users")
        for user in active_users:
            print(f"   - {user.username}")
        print()

        print("3. Getting user count by status:")
        status_counts = User.get_user_count_by_status(connection=connection)
        for status_count in status_counts:
            print(f"   - {status_count.status}: {status_count.user_count}")
        print()

        print("4. Creating a new user (with transaction):")
        with engine.connect() as tx_conn:
            with tx_conn.begin():
                result = User.create_user(
                    connection=tx_conn,
                    username="alice_jones",
                    email="alice@example.com",
                    password_hash="hashed_password_999",
                    status="active",
                )
                new_user_id = result.fetchone()[0]
                print(f"   Created user with ID: {new_user_id}")
        print()

        print("5. Updating user status:")
        with engine.connect() as tx_conn:
            with tx_conn.begin():
                User.update_user_status(
                    connection=tx_conn, user_id=3, new_status="active"
                )
                print("   Updated user status")
        print()

        print("6. Verifying the update:")
        updated_users = User.get_users_by_status(connection=connection, status="active")
        print(f"   Now have {len(updated_users)} active users")


def show_logger_benefits():
    """Show the benefits of the simplified logger approach."""
    print("\n=== Benefits of Simplified Logger ===")
    print("✅ No optional logger parameter in method signatures")
    print("✅ Consistent logging behavior across all methods")
    print("✅ Class-level logger follows Python best practices")
    print("✅ Cleaner, more maintainable generated code")
    print("✅ Simpler API for users")
    print("✅ Automatic error logging with proper context")


def main():
    """Main example function."""
    print("splurge-sql-generator Simple Example")
    print("=" * 50)
    print()

    # Demonstrate the simplified logger
    demonstrate_simplified_logger()

    # Show benefits
    show_logger_benefits()

    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print(
        "\nThe simplified logger approach makes the API cleaner and more maintainable."
    )


if __name__ == "__main__":
    main()
