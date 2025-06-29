#!/usr/bin/env python3
"""
Usage Example for jpy-sql-generator

This example demonstrates how to use the generated classes with the simplified logger approach.
"""

import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

# Import the generated classes
from output.User import User
from output.ProductRepository import ProductRepository
from output.OrderService import OrderService


def setup_database():
    """Create a test database and tables."""
    engine = create_engine('sqlite:///example.db')
    
    with engine.connect() as conn:
        # Create tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
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
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """))
        
        conn.commit()
    
    return engine


def setup_logging():
    """Configure logging to see the class-level logger in action."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demonstrate_user_operations(connection: Connection):
    """Demonstrate User class operations with simplified logger."""
    print("\n=== User Operations ===")
    
    # Create users
    with connection.begin():
        result = User.create_user(
            connection=connection,
            username='john_doe',
            email='john@example.com',
            password_hash='hashed_password_123',
            status='active'
        )
        print(f"Created user with ID: {result.fetchone()[0]}")
        
        result = User.create_user(
            connection=connection,
            username='jane_smith',
            email='jane@example.com',
            password_hash='hashed_password_456',
            status='active'
        )
        print(f"Created user with ID: {result.fetchone()[0]}")
    
    # Fetch users
    users = User.get_users_by_status(connection=connection, status='active')
    print(f"Found {len(users)} active users:")
    for user in users:
        print(f"  - {user.username} ({user.email})")
    
    # Get user count by status
    status_counts = User.get_user_count_by_status(connection=connection)
    print("User counts by status:")
    for status_count in status_counts:
        print(f"  - {status_count.status}: {status_count.user_count}")


def demonstrate_product_operations(connection: Connection):
    """Demonstrate ProductRepository class operations."""
    print("\n=== Product Operations ===")
    
    # Create products
    with connection.begin():
        result = ProductRepository.create_product(
            connection=connection,
            name='Laptop',
            description='High-performance laptop',
            price=999.99,
            category_id=1,
            stock_quantity=10
        )
        print(f"Created product with ID: {result.fetchone()[0]}")
        
        result = ProductRepository.create_product(
            connection=connection,
            name='Mouse',
            description='Wireless mouse',
            price=29.99,
            category_id=1,
            stock_quantity=50
        )
        print(f"Created product with ID: {result.fetchone()[0]}")
    
    # Search products
    products = ProductRepository.search_products(
        connection=connection,
        search_term='%laptop%'
    )
    print(f"Found {len(products)} products matching 'laptop':")
    for product in products:
        print(f"  - {product.name}: ${product.price}")
    
    # Check low stock
    low_stock = ProductRepository.get_low_stock_products(
        connection=connection,
        threshold=20
    )
    print(f"Found {len(low_stock)} products with low stock:")
    for product in low_stock:
        print(f"  - {product.name}: {product.stock_quantity} in stock")


def demonstrate_order_operations(connection: Connection):
    """Demonstrate OrderService class operations."""
    print("\n=== Order Operations ===")
    
    # Create an order
    with connection.begin():
        result = OrderService.create_order(
            connection=connection,
            user_id=1,
            total_amount=1029.98,
            status='pending'
        )
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
    print("- User.logger: jpy_sql_generator.output.User.User")
    print("- ProductRepository.logger: jpy_sql_generator.output.ProductRepository.ProductRepository")
    print("- OrderService.logger: jpy_sql_generator.output.OrderService.OrderService")
    print("\nNo need to pass logger parameters - it's handled automatically!")


def main():
    """Main example function."""
    print("jpy-sql-generator Usage Example")
    print("=" * 50)
    
    # Setup logging to see the class-level loggers in action
    setup_logging()
    
    # Create database and tables
    engine = setup_database()
    
    with engine.connect() as connection:
        # Demonstrate the simplified logger approach
        demonstrate_logger_behavior()
        
        # Demonstrate operations with each generated class
        demonstrate_user_operations(connection)
        demonstrate_product_operations(connection)
        demonstrate_order_operations(connection)
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nKey benefits of the simplified logger approach:")
    print("- Cleaner method signatures (no optional logger parameter)")
    print("- Consistent logging behavior across all methods")
    print("- Class-level logger follows Python best practices")
    print("- Reduced complexity in generated code")


if __name__ == "__main__":
    main() 