-- Add a table for animals potentially detected by gate
CREATE TABLE IF NOT EXISTS detected_animals (
    time_stamp TIMESTAMP DEFAULT NOW(),
    animal_id SERIAL PRIMARY KEY,
    animal_type VARCHAR(255) NOT NULL,
    animal_name VARCHAR(255) NOT NULL,
    is_endangered BOOLEAN NOT NULL,
    is_threat BOOLEAN NOT NULL
);

-- Provide some mock data to show what animals are potentially detected
INSERT INTO detected_animals (animal_type, animal_name, is_endangered, is_threat)
VALUES
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Amur Leopard', TRUE, TRUE),
    ('Mammal', 'Black Rhino', TRUE, FALSE),
    ('Mammal', 'Black Rhino', TRUE, FALSE),
    ('Mammal', 'Black Rhino', TRUE, FALSE),
    ('Mammal', 'Black Rhino', TRUE, FALSE),
    ('Mammal', 'Black Rhino', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Orangutan', TRUE, FALSE),
    ('Mammal', 'Giant Panda', TRUE, FALSE),
    ('Mammal', 'Giant Panda', TRUE, FALSE),
    ('Mammal', 'Giant Panda', TRUE, FALSE),
    ('Mammal', 'Giant Panda', TRUE, FALSE),
    ('Mammal', 'Giant Panda', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Asian Elephant', TRUE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Dog', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Cat', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Fox', FALSE, FALSE),
    ('Mammal', 'Snow Leopard', TRUE, TRUE);

-- Creating some predictable data for alerts
CREATE TYPE alert_level_enum AS ENUM ('info', 'warning', 'critical')

-- Add table for alerts 
CREATE TABLE IF NOT EXISTS alerts (
    alert_no SERIAL PRIMARY KEY,
    alert_desc TEXT,
    alert_level alert_level_enum,
    date_and_time TIMESTAMP DEFAULT NOW()
);

-- Creating some predictable data for gates
CREATE TYPE gate_status_enum AS ENUM ('opened', 'closed')
CREATE TYPE gate_condition_enum AS ENUM ('unavailable', 'available')

-- Add table for gates
CREATE TABLE IF NOT EXISTS gates (
    gate_no SERIAL PRIMARY KEY,
    gate_status gate_status_enum, -- opened or closed
    gate_condition gate_condition_enum
)
