# City

# create_table
CREATE TABLE IF NOT EXISTS city (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(128) NOT NULL,
    alias VARCHAR(128) NOT NULL,
    county_alias VARCHAR(128) NOT NULL,
    state_alias VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY (state_alias, county_alias, alias)
    UNIQUE KEY (state_alias, county_alias, name)
    FOREIGN KEY (state_alias) REFERENCES state(alias)
    FOREIGN KEY (county_alias) REFERENCES county(alias)
);

# insert_city
INSERT INTO city (id, name, alias, county_alias, state_alias, created_at, updated_at) 
VALUES (
    :id,
    :name,  
    :alias,
    :county_alias,
    :state_alias,
    NOW(),
    NOW()
);

# update_city
UPDATE city 
SET 
    name = :name, 
    alias = :alias, 
    county_alias = :county_alias, 
    state_alias = :state_alias, 
    updated_at = NOW() 
WHERE id = :id;

# get_city_by_id
SELECT * 
FROM city 
WHERE id = :id;

# get_city_by_alias_and_county_alias_and_state_alias
SELECT * 
FROM city 
WHERE 
    alias = :alias 
    AND county_alias = :county_alias 
    AND state_alias = :state_alias;

# get_cities_by_county_alias_and_state_alias
SELECT * 
FROM city 
WHERE 
    county_alias = :county_alias 
    AND state_alias = :state_alias 
    ORDER BY name;

# get_cities_by_state_alias
SELECT * 
FROM city 
WHERE state_alias = :state_alias 
ORDER BY county_alias, name;

# get_all_cities
SELECT * 
FROM city 
ORDER BY state_alias, county_alias, name;
