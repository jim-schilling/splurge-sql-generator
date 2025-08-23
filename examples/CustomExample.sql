# CustomExample

#get_item_by_id
SELECT id, name, amount, is_active, metadata, binary_data
FROM custom_items
WHERE id = :id;

#create_item
INSERT INTO custom_items (name, amount, is_active, metadata, binary_data)
VALUES (:name, :amount, :is_active, :metadata, :binary_data)
RETURNING id;

#update_item_amount
UPDATE custom_items
SET amount = :new_amount
WHERE id = :id;
