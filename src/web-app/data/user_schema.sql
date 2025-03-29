-- Create the users table with a foreign key reference to the roles table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,      -- User ID
    username VARCHAR(255) NOT NULL,   -- Username
    role_id INTEGER NOT NULL,         -- Foreign key to the roles table (added NOT NULL for integrity)
    FOREIGN KEY (role_id) REFERENCES roles(role_id)  -- Link users to roles
);

-- Create the roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY,          -- Role ID
    role_name VARCHAR(255) NOT NULL       -- Role name (e.g., 'admin', 'user', etc.)
);

-- Insert roles into the roles table with specific role_id values
INSERT INTO roles (role_id, role_name) 
VALUES 
    (0, 'user'),  -- role_id 0 
    (1, 'admin'); -- role_id 1

-- Create the perms table for permissions
CREATE TABLE IF NOT EXISTS perms (
    perm_id SERIAL PRIMARY KEY,           -- Permission ID (auto-increment)
    perm_name VARCHAR(255) NOT NULL       -- Permission name (e.g., 'view_gate', 'open_gate', etc.)
);

-- Insert permissions into the perms table
INSERT INTO perms (perm_name)
VALUES
    ('view_gate'), -- 0
    ('view_alerts'), -- 1
    ('view_stats'), -- 2
    ('open_gate'), -- 3
    ('close_gate'), -- 4
    ('db_control'); -- 5

-- Create a join table between roles and permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,                 -- Foreign key to the roles table
    permission_id INTEGER NOT NULL,           -- Foreign key to the permissions table
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (permission_id) REFERENCES perms(perm_id),
    CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id)  -- Ensure uniqueness of role-permission pairs
);

INSERT INTO role_permissions (role_id, permission_id)
VALUES
    (0, 0), -- user has view_gate
    (1, 0), -- admin has view_gate
    (0, 1), -- user has view_alerts
    (1, 1), -- admin has view_alerts
    (0, 2), -- user has view_stats
    (1, 2), -- admin has view_stats
    (1, 3), -- admin has open_gate
    (1, 4), -- admin has close_gate
    (1, 5); -- admin has db_control


