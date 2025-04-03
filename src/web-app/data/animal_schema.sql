CREATE TABLE IF NOT EXISTS species_list (
    species_id SERIAL PRIMARY KEY,
    species_name VARCHAR(255) UNIQUE NOT NULL,
    is_endangered BOOLEAN NOT NULL,
    is_threat BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS animals (
    animal_id SERIAL PRIMARY KEY,
    animal_type VARCHAR(255) NOT NULL,
    species_id INT REFERENCES species_list(species_id) ON DELETE SET NULL,
    has_detected BOOLEAN DEFAULT FALSE,
    has_entered BOOLEAN DEFAULT FALSE,
    is_friendly BOOLEAN NOT NULL
);

