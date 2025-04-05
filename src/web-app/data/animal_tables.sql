CREATE TABLE IF NOT EXISTS animals (
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    animal_id SERIAL PRIMARY KEY,
    animal_type VARCHAR(255) NOT NULL,
    species_name VARCHAR(255) NOT NULL,
    is_endangered BOOLEAN NOT NULL,
    is_threat BOOLEAN NOT NULL
);


-- Add sql functions to get statistics about the animals

