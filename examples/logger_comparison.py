#!/usr/bin/env python3
"""
Logger Comparison Example

This example shows the difference between the old and new logger approaches.
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
    """Configure logging to demonstrate the class-level logger."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def demonstrate_old_approach():
    """Show how the old approach would have looked (with optional logger parameter)."""
    print("=== OLD APPROACH (Before 0.2.2) ===")
    print("Method signatures would have looked like:")
    print(
        """
    @classmethod
    def get_user_by_id(
        cls,
        *,
        connection: Connection,
        user_id: Any,
        logger: Optional[logging.Logger] = None,  # <- Optional parameter
    ) -> List[Row]:
        if logger is None:
            logger = cls.logger  # <- Conditional assignment
        # ... rest of method
    """
    )
    print("Usage would have been:")
    print(
        """
    # Option 1: Use default logger
    users = User.get_user_by_id(
        connection=connection,
        user_id=1,
    )
    
    # Option 2: Pass custom logger
    custom_logger = logging.getLogger('my.custom.logger')
    users = User.get_user_by_id(
        connection=connection,
        user_id=1,
        logger=custom_logger,
    )
    """
    )


def demonstrate_new_approach():
    """Show the new simplified approach."""
    print("\n=== NEW APPROACH (0.2.2+) ===")
    print("Method signatures now look like:")
    print(
        """
    @classmethod
    def get_user_by_id(
        cls,
        *,
        connection: Connection,
        user_id: Any,
    ) -> List[Row]:
        logger = cls.logger  # <- Direct assignment, no conditional
        # ... rest of method
    """
    )
    print("Usage is now simpler:")
    print(
        """
    # Always uses class-level logger - no optional parameter needed
    users = User.get_user_by_id(
        connection=connection,
        user_id=1,
    )
    """
    )


def demonstrate_actual_usage():
    """Show actual usage with the new approach."""
    print("\n=== ACTUAL USAGE EXAMPLE ===")

    # Create a simple in-memory database
    engine = create_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        # Create a simple table
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT
            )
        """
            )
        )

        # Insert test data
        conn.execute(
            text(
                """
            INSERT INTO users (id, username, email) VALUES 
            (1, 'john_doe', 'john@example.com'),
            (2, 'jane_smith', 'jane@example.com')
        """
            )
        )
        conn.commit()

        print("Executing User.get_user_by_id with new logger approach...")
        print("(Check the log output above to see the class-level logger in action)")

        # This will use the class-level logger automatically
        users = User.get_user_by_id(connection=conn, user_id=1)

        if users:
            user = users[0]
            print(f"Found user: {user.username} ({user.email})")
        else:
            print("No user found")


def show_benefits():
    """Show the benefits of the new approach."""
    print("\n=== BENEFITS OF THE NEW APPROACH ===")
    print("✅ Cleaner method signatures (fewer parameters)")
    print("✅ Consistent logging behavior across all methods")
    print("✅ No conditional logic for logger assignment")
    print("✅ Follows Python utility class best practices")
    print("✅ Reduced complexity in generated code")
    print("✅ Better maintainability")
    print("✅ Simpler API for users")


def main():
    """Main comparison function."""
    print("splurge-sql-generator Logger Comparison")
    print("=" * 50)

    # Setup logging to see the class-level logger in action
    setup_logging()

    # Show the differences
    demonstrate_old_approach()
    demonstrate_new_approach()

    # Show actual usage
    demonstrate_actual_usage()

    # Show benefits
    show_benefits()

    print("\n" + "=" * 50)
    print("The new approach is simpler, cleaner, and more maintainable!")


if __name__ == "__main__":
    main()
