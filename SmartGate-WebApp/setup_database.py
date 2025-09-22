#!/usr/bin/env python3
"""
Database setup script for SmartGate WebApp
Run this script to initialize the command logging tables
"""

import os
import psycopg
from pathlib import Path

def get_db_connection():
    """Get database connection"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def run_sql_file(file_path):
    """Run SQL commands from a file"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open(file_path, 'r') as file:
            sql_content = file.read()
            
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:50]}...")
                cursor.execute(statement)
        
        conn.commit()
        print(f"Successfully executed SQL file: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error executing SQL file {file_path}: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main setup function"""
    print("SmartGate WebApp Database Setup")
    print("=" * 40)
    
    # Check if command schema file exists
    schema_file = Path("models/command_schema.sql")
    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}")
        return False
    
    # Run the command schema
    print("Setting up command logging tables...")
    if run_sql_file(schema_file):
        print("✅ Database setup completed successfully!")
        return True
    else:
        print("❌ Database setup failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

