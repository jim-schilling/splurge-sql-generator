# ProductRepository
# get_product_by_id
SELECT id, name, description, price, category_id, stock_quantity, created_at 
FROM products 
WHERE id = :product_id;

# get_products_by_category
SELECT id, name, description, price, stock_quantity 
FROM products 
WHERE category_id = :category_id 
ORDER BY name;

# search_products
-- Use LIKE for SQLite compatibility (case-insensitive if the DB is configured accordingly)
SELECT id, name, description, price, category_id 
FROM products 
WHERE name LIKE :search_term OR description LIKE :search_term 
ORDER BY name;

# create_product
INSERT INTO products (name, description, price, category_id, stock_quantity) 
VALUES (:name, :description, :price, :category_id, :stock_quantity) 
RETURNING id;

# update_product_stock
UPDATE products 
SET stock_quantity = :new_quantity, updated_at = CURRENT_TIMESTAMP 
WHERE id = :product_id;

# get_low_stock_products
SELECT id, name, stock_quantity 
FROM products 
WHERE stock_quantity <= :threshold 
ORDER BY stock_quantity ASC; 