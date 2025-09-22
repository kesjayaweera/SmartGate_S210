-- Command logging table for tracking all gate operations
CREATE TABLE IF NOT EXISTS command_logs (
    command_id VARCHAR(36) PRIMARY KEY,
    command_type VARCHAR(50) NOT NULL,
    gate_no INTEGER,
    user_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_command_logs_gate_no ON command_logs(gate_no);
CREATE INDEX IF NOT EXISTS idx_command_logs_status ON command_logs(status);
CREATE INDEX IF NOT EXISTS idx_command_logs_user_id ON command_logs(user_id);

-- Add current_operation and operation_start_time to gates table
ALTER TABLE gates ADD COLUMN IF NOT EXISTS current_operation VARCHAR(50);
ALTER TABLE gates ADD COLUMN IF NOT EXISTS operation_start_time TIMESTAMP;

-- Update gates table to track current operations
UPDATE gates SET current_operation = NULL, operation_start_time = NULL WHERE current_operation IS NULL;

