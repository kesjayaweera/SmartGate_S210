-- Create the roles table (This should be created first so that roles exist before referencing them in users)
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,          -- Role ID with SERIAL for auto-increment, starts at 1 by default
    role_name VARCHAR(255) NOT NULL      -- Role name (e.g., 'admin', 'user', etc.)
);

-- Insert roles into the roles table with specific role_id values
INSERT INTO roles (role_name) 
VALUES 
    ('user'),  -- role_id 1 (auto-generated)
    ('admin'); -- role_id 2 (auto-generated)

-- Create the users table with a foreign key reference to the roles table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,      -- User ID as BIGINT
    username VARCHAR(255) NOT NULL,   -- Username
    role_id INTEGER NOT NULL,         -- Foreign key to the roles table (added NOT NULL for integrity)
    FOREIGN KEY (role_id) REFERENCES roles(role_id)  -- Link users to roles
);

-- Create the perms table for permissions
CREATE TABLE IF NOT EXISTS perms (
    perm_id SERIAL PRIMARY KEY,           -- Permission ID (auto-increment, starts at 1 by default)
    perm_name VARCHAR(255) NOT NULL       -- Permission name (e.g., 'view_gate', 'open_gate', etc.)
);

-- Insert permissions into the perms table
INSERT INTO perms (perm_name)
VALUES
    ('view_gate'),    -- permission_id 1
    ('view_alerts'),  -- permission_id 2
    ('view_stats'),   -- permission_id 3
    ('open_gate'),    -- permission_id 4
    ('close_gate'),   -- permission_id 5
    ('db_control');   -- permission_id 6

-- Create a join table between roles and permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,                 -- Foreign key to the roles table
    permission_id INTEGER NOT NULL,           -- Foreign key to the permissions table
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (permission_id) REFERENCES perms(perm_id),
    CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id)  -- Ensure uniqueness of role-permission pairs
);

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
VALUES
    (1, 1), -- user has view_gate
    (2, 1), -- admin has view_gate
    (1, 2), -- user has view_alerts
    (2, 2), -- admin has view_alerts
    (1, 3), -- user has view_stats
    (2, 3), -- admin has view_stats
    (2, 4), -- admin has open_gate
    (2, 5), -- admin has close_gate
    (2, 6); -- admin has db_control
