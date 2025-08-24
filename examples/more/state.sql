# State

# create_table
CREATE TABLE IF NOT EXISTS state (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(128) NOT NULL,
    alias VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY (alias)
);

# insert_state
INSERT INTO state (id, name, alias, created_at, updated_at) 
VALUES (
    :id,
    :name,
    :alias,
    NOW(),
    NOW()
);

# update_state
UPDATE state 
SET 
    name = :name, 
    alias = :alias, 
    updated_at = NOW() 
WHERE id = :id;

# get_state_by_id
SELECT * 
FROM state 
WHERE id = :id;

# get_state_by_alias
SELECT * 
FROM state 
WHERE alias = :alias;

# get_all_states
SELECT * 
FROM state
ORDER BY name;
