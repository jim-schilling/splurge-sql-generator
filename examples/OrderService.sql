# get_order_by_id
SELECT o.id, o.user_id, o.total_amount, o.status, o.created_at,
       u.username, u.email
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.id = :order_id;

# get_user_orders
SELECT id, total_amount, status, created_at 
FROM orders 
WHERE user_id = :user_id 
ORDER BY created_at DESC;

# create_order
INSERT INTO orders (user_id, total_amount, status) 
VALUES (:user_id, :total_amount, :status) 
RETURNING id;

# update_order_status
UPDATE orders 
SET status = :new_status, updated_at = CURRENT_TIMESTAMP 
WHERE id = :order_id;

# get_order_items
SELECT oi.id, oi.product_id, oi.quantity, oi.price,
       p.name as product_name
FROM order_items oi
JOIN products p ON oi.product_id = p.id
WHERE oi.order_id = :order_id;

# get_revenue_by_date_range
SELECT DATE(created_at) as order_date, 
       SUM(total_amount) as daily_revenue,
       COUNT(*) as order_count
FROM orders 
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY DATE(created_at)
ORDER BY order_date; 