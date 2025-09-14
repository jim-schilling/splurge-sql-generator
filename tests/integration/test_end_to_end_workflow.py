"""
End-to-end workflow tests for splurge-sql-generator.

These tests focus on complete end-to-end workflows.
"""

import ast

import pytest

from splurge_sql_generator.code_generator import PythonCodeGenerator
from tests.unit.test_utils import (
    temp_sql_files,
    assert_generated_code_structure,
    assert_method_parameters,
)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_workflow_with_schema_inference(self) -> None:
        """Test complete workflow from SQL to executable Python code."""
        # Create comprehensive test case
        sql_content = """# ProductRepository
# get_product_by_id
SELECT id, name, price, category_id, created_at 
FROM products 
WHERE id = :product_id;

# get_products_by_category
SELECT id, name, price 
FROM products 
WHERE category_id = :category_id 
ORDER BY name;

# create_product
INSERT INTO products (name, price, category_id, description) 
VALUES (:name, :price, :category_id, :description) 
RETURNING id;

# update_product_price
UPDATE products 
SET price = :new_price, updated_at = CURRENT_TIMESTAMP 
WHERE id = :product_id;

# delete_product
DELETE FROM products 
WHERE id = :product_id;

# get_product_stats
SELECT 
    category_id,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products 
GROUP BY category_id;
"""

        schema_content = """CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""

        with temp_sql_files(sql_content, schema_content) as (sql_file, schema_file):
            # Generate code
            generator = PythonCodeGenerator()
            generated_code = generator.generate_class(
                sql_file, schema_file_path=schema_file
            )

            # Validate complete class structure
            expected_methods = [
                "get_product_by_id",
                "get_products_by_category",
                "create_product",
                "update_product_price",
                "delete_product",
                "get_product_stats",
            ]

            assert_generated_code_structure(
                generated_code, "ProductRepository", expected_methods
            )

            # Validate method parameters
            assert_method_parameters(
                generated_code, "get_product_by_id", ["product_id"]
            )
            assert_method_parameters(
                generated_code, "get_products_by_category", ["category_id"]
            )
            assert_method_parameters(
                generated_code,
                "create_product",
                ["name", "price", "category_id", "description"],
            )
            assert_method_parameters(
                generated_code, "update_product_price", ["new_price", "product_id"]
            )
            assert_method_parameters(generated_code, "delete_product", ["product_id"])
            assert_method_parameters(generated_code, "get_product_stats", [])

            # Validate SQL content preservation
            assert "SELECT id, name, price, category_id, created_at" in generated_code
            assert "ORDER BY name" in generated_code
            assert "GROUP BY category_id" in generated_code
            assert "AVG(price) as avg_price" in generated_code

            # Validate Python syntax and structure
            try:
                tree = ast.parse(generated_code)

                # Validate class definition
                class_defs = [
                    node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                ]
                assert len(class_defs) == 1
                assert class_defs[0].name == "ProductRepository"

                # Validate method definitions
                method_defs = [
                    node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                ]
                assert len(method_defs) == len(expected_methods)

            except SyntaxError as e:
                pytest.fail(f"Generated code has syntax error: {e}")
