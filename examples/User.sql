# User
# get_user_by_id
SELECT id, username, email, created_at 
FROM users 
WHERE id = :user_id;

# get_users_by_status
SELECT id, username, email, status, created_at 
FROM users 
WHERE status = :status 
ORDER BY created_at DESC;

# create_user
INSERT INTO users (username, email, password_hash, status) 
VALUES (:username, :email, :password_hash, :status) 
RETURNING id;

# update_user_status
UPDATE users 
SET status = :new_status, updated_at = CURRENT_TIMESTAMP 
WHERE id = :user_id;

# delete_user
DELETE FROM users 
WHERE id = :user_id;

# get_user_count_by_status
SELECT status, COUNT(*) as user_count 
FROM users 
GROUP BY status; 