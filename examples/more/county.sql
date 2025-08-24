# County

# create_table
CREATE TABLE IF NOT EXISTS county (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(128) NOT NULL,
    alias VARCHAR(128) NOT NULL, 
    state_alias VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY (state_alias, alias)
    UNIQUE KEY (state_alias, name)
    FOREIGN KEY (state_alias) REFERENCES state(alias)
);

# insert_county
INSERT INTO county (id, name, alias, state_alias, created_at, updated_at) 
VALUES (
    :id,
    :name,
    :alias,
    :state_alias,
    NOW(),
    NOW()
);

# update_county
UPDATE county 
SET 
    name = :name, 
    alias = :alias, 
    state_alias = :state_alias, 
    updated_at = NOW() 
WHERE id = :id;

# get_county_by_id
SELECT * 
FROM county 
WHERE id = :id;

# get_county_by_alias_and_state_alias
SELECT * 
FROM county 
WHERE alias = :alias 
    AND state_alias = :state_alias;

# get_county_by_name_and_state_alias
SELECT * 
FROM county 
WHERE name = :name 
    AND state_alias = :state_alias;

# get_all_counties_by_state_alias
SELECT * 
FROM county 
WHERE state_alias = :state_alias
ORDER BY name;

# get_all_counties
SELECT * 
FROM county
ORDER BY state_alias, name;




