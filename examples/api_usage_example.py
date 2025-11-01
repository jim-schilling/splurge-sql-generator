#!/usr/bin/env python3
"""
Usage Example for splurge-sql-generator

This example demonstrates how to use the generated classes with the simplified logger approach.
"""

import logging
import os
import shutil
import sys
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from splurge_sql_generator import generate_class
from splurge_sql_generator.utils import to_snake_case

# Add the project root to the path so we can import from the package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_generated_classes() -> str:
    """Generate all example classes into a temporary directory.

    Returns:
        Path to the temporary directory containing generated classes
    """
    temp_dir = tempfile.mkdtemp()

    # Create __init__.py to make it a package
    init_file = os.path.join(temp_dir, "__init__.py")
    with open(init_file, "w", encoding="utf-8") as f:
        f.write("")

    # Generate each required module
    mapping = {
        "User": (
            os.path.join(PROJECT_ROOT, "examples", "User.sql"),
            os.path.join(PROJECT_ROOT, "examples", "User.schema"),
        ),
        "ProductRepository": (
            os.path.join(PROJECT_ROOT, "examples", "ProductRepository.sql"),
            os.path.join(PROJECT_ROOT, "examples", "ProductRepository.schema"),
        ),
        "OrderService": (
            os.path.join(PROJECT_ROOT, "examples", "OrderService.sql"),
            os.path.join(PROJECT_ROOT, "examples", "OrderService.schema"),
        ),
    }

    for module_name, (sql_path, schema_path) in mapping.items():
        snake_case_name = to_snake_case(module_name)
        py_path = os.path.join(temp_dir, f"{snake_case_name}.py")
        generate_class(sql_path, output_file_path=py_path, schema_file_path=schema_path)

    return temp_dir


def setup_database():
    """Create a test database and tables. Resets DB file each run for repeatability."""
    db_path = os.path.join(PROJECT_ROOT, "example.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        # Create tables
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category_id INTEGER,
                stock_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """
            )
        )

        conn.commit()

    return engine


def setup_logging():
    """Configure logging to see the class-level logger in action."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def demonstrate_user_operations(connection: Connection) -> None:
    """Demonstrate User class operations with simplified logger."""
    print("\n=== User Operations ===")
    from user import User  # local import after generation

    # Create users
    with connection.begin():
        result = User.create_user(
            connection=connection,
            username="john_doe",
            email="john@example.com",
            password_hash="hashed_password_123",
            status="active",
        )
        print(f"Created user with ID: {result.fetchone()[0]}")

        result = User.create_user(
            connection=connection,
            username="jane_smith",
            email="jane@example.com",
            password_hash="hashed_password_456",
            status="active",
        )
        print(f"Created user with ID: {result.fetchone()[0]}")

    # Fetch users
    users = User.get_users_by_status(connection=connection, status="active")
    print(f"Found {len(users)} active users:")
    for user in users:
        print(f"  - {user.username} ({user.email})")

    # Get user count by status
    status_counts = User.get_user_count_by_status(connection=connection)
    print("User counts by status:")
    for status_count in status_counts:
        print(f"  - {status_count.status}: {status_count.user_count}")


def demonstrate_product_operations(connection: Connection) -> None:
    """Demonstrate ProductRepository class operations."""
    print("\n=== Product Operations ===")
    from product_repository import (
        ProductRepository,
    )  # local import after generation

    # Create products
    with connection.begin():
        result = ProductRepository.create_product(
            connection=connection,
            name="Laptop",
            description="High-performance laptop",
            price=999.99,
            category_id=1,
            stock_quantity=10,
        )
        print(f"Created product with ID: {result.fetchone()[0]}")

        result = ProductRepository.create_product(
            connection=connection,
            name="Mouse",
            description="Wireless mouse",
            price=29.99,
            category_id=1,
            stock_quantity=50,
        )
        print(f"Created product with ID: {result.fetchone()[0]}")

    # Search products
    products = ProductRepository.search_products(connection=connection, search_term="%laptop%")
    print(f"Found {len(products)} products matching 'laptop':")
    for product in products:
        print(f"  - {product.name}: ${product.price}")

    # Check low stock
    low_stock = ProductRepository.get_low_stock_products(connection=connection, threshold=20)
    print(f"Found {len(low_stock)} products with low stock:")
    for product in low_stock:
        print(f"  - {product.name}: {product.stock_quantity} in stock")


def demonstrate_order_operations(connection: Connection) -> None:
    """Demonstrate OrderService class operations."""
    print("\n=== Order Operations ===")
    from order_service import OrderService  # local import after generation

    # Create an order
    with connection.begin():
        result = OrderService.create_order(connection=connection, user_id=1, total_amount=1029.98, status="pending")
        order_id = result.fetchone()[0]
        print(f"Created order with ID: {order_id}")

    # Get order details
    orders = OrderService.get_order_by_id(connection=connection, order_id=order_id)
    if orders:
        order = orders[0]
        print(f"Order {order.id}: ${order.total_amount} - {order.status}")
        print(f"  Customer: {order.username} ({order.email})")

    # Get user orders
    user_orders = OrderService.get_user_orders(connection=connection, user_id=1)
    print(f"User has {len(user_orders)} orders:")
    for order in user_orders:
        print(f"  - Order {order.id}: ${order.total_amount} ({order.status})")


def demonstrate_logger_behavior():
    """Demonstrate the simplified logger approach."""
    print("\n=== Logger Behavior ===")
    print("Notice that all operations use the same class-level logger:")
    print("- User.logger: output.User.User")
    print("- ProductRepository.logger: output.ProductRepository.ProductRepository")
    print("- OrderService.logger: output.OrderService.OrderService")
    print("\nNo need to pass logger parameters - it's handled automatically!")


def main():
    """Main example function."""
    print("splurge-sql-generator Usage Example")
    print("=" * 50)

    # Setup logging to see the class-level loggers in action
    setup_logging()

    # Generate classes to temporary directory
    temp_dir = _ensure_generated_classes()

    try:
        # Add temp directory to path so we can import
        sys.path.insert(0, temp_dir)

        # Create database and tables
        engine = setup_database()

        # Demonstrate the simplified logger approach
        demonstrate_logger_behavior()

        # Use separate connections to avoid nested/implicit transaction conflicts
        with engine.connect() as connection:
            demonstrate_user_operations(connection)

        with engine.connect() as connection:
            demonstrate_product_operations(connection)

        with engine.connect() as connection:
            demonstrate_order_operations(connection)

        print("\n" + "=" * 50)
        print("Example completed successfully!")
        print("\nKey benefits of the simplified logger approach:")
        print("- Cleaner method signatures (no optional logger parameter)")
        print("- Consistent logging behavior across all methods")
        print("- Class-level logger follows Python best practices")
        print("- Reduced complexity in generated code")

    finally:
        # Remove from path and cleanup
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
