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
    role_id INTEGER NOT NULL REFERENCES roles(role_id) -- Foreign key to the roles table (added NOT NULL for integrity) Link users to roles
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
    ('data_control');   -- permission_id 6

-- Create a join table between roles and permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(role_id),       -- Foreign key to the roles table
    permission_id INTEGER NOT NULL REFERENCES perms(perm_id), -- Foreign key to the permissions table
    CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id)  -- Ensure uniqueness of role-permission pairs
);

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
VALUES
    (1, 1), (2, 1), -- user and admin has view_gate
    (1, 2), (2, 2), -- user and admin has view_alerts
    (1, 3), (2, 3), -- user and admin has view_stats
    (2, 4), (2, 5), (2, 6); -- admin has open_gate, close_gate, data_control

CREATE TABLE IF NOT EXISTS user_perms (
    username VARCHAR(255) NOT NULL, 
    name_of_role VARCHAR(255) NOT NULL,
    permissions TEXT NOT NULL, 
    PRIMARY KEY (username, name_of_role)
);

CREATE OR REPLACE FUNCTION refresh_user_perms(user_id BIGINT)
RETURNS void AS $$
BEGIN
    -- Remove existing permissions for the user (if any)
    DELETE FROM user_perms 
    WHERE username = (SELECT username FROM users WHERE users.user_id = $1);

    -- Insert or update the permissions based on the current role
    INSERT INTO user_perms (username, name_of_role, permissions)
    SELECT
        u.username,
        r.role_name,
        STRING_AGG(p.perm_name, ',') AS permissions
    FROM users u -- This gets the username from the users relation
    JOIN roles r ON u.role_id = r.role_id -- This gets the role_name according to the user based on role_id
    JOIN role_permissions rp ON r.role_id = rp.role_id -- This gets the permission_id that the role have 
    JOIN perms p ON rp.permission_id = p.perm_id -- This join get the permision names of the role based on what permission the role has
    WHERE u.user_id = $1  -- Use the parameter directly here
    GROUP BY u.username, r.role_name
    ON CONFLICT (username, name_of_role) DO UPDATE 
    SET permissions = EXCLUDED.permissions;
END;
$$ LANGUAGE plpgsql;



