#!/usr/bin/env python3
"""
Database migration script to add fund_type column to tefas_fund_info table
and populate existing records based on download history.

This script:
1. Adds the fund_type column to tefas_fund_info table
2. Populates existing records with fund_type based on download history
3. Creates an index on the fund_type column for better query performance
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def get_database_path() -> str:
    """Get the database path from environment or use default."""
    db_path = os.environ.get("DATABASE_NAME", "finance_tools.db")
    if not os.path.isabs(db_path):
        # If relative path, make it relative to the project root
        project_root = Path(__file__).parent
        db_path = str(project_root / db_path)
    return db_path

def add_fund_type_column(cursor: sqlite3.Cursor) -> None:
    """Add fund_type column to tefas_fund_info table."""
    print("Adding fund_type column to tefas_fund_info table...")
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tefas_fund_info)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fund_type' in columns:
            print("fund_type column already exists, skipping...")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE tefas_fund_info 
            ADD COLUMN fund_type VARCHAR(10)
        """)
        print("✅ fund_type column added successfully")
        
    except sqlite3.Error as e:
        print(f"❌ Error adding fund_type column: {e}")
        raise

def create_fund_type_index(cursor: sqlite3.Cursor) -> None:
    """Create index on fund_type column for better query performance."""
    print("Creating index on fund_type column...")
    
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tefas_fund_info_fund_type 
            ON tefas_fund_info(fund_type)
        """)
        print("✅ fund_type index created successfully")
        
    except sqlite3.Error as e:
        print(f"❌ Error creating fund_type index: {e}")
        raise

def get_fund_type_mapping(cursor: sqlite3.Cursor) -> Dict[str, str]:
    """Get mapping of fund codes to fund types from download history."""
    print("Building fund type mapping from download history...")
    
    fund_type_mapping = {}
    
    try:
        # Query download history to get fund type mappings
        cursor.execute("""
            SELECT DISTINCT funds, kind 
            FROM download_history 
            WHERE data_type = 'tefas' 
            AND funds IS NOT NULL 
            AND kind IN ('BYF', 'YAT', 'EMK')
        """)
        
        rows = cursor.fetchall()
        
        for funds_json, kind in rows:
            if funds_json:
                import json
                try:
                    funds = json.loads(funds_json)
                    if isinstance(funds, list):
                        for fund_code in funds:
                            fund_type_mapping[fund_code] = kind
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse funds JSON: {funds_json}")
                    continue
        
        print(f"✅ Found {len(fund_type_mapping)} fund type mappings")
        return fund_type_mapping
        
    except sqlite3.Error as e:
        print(f"❌ Error building fund type mapping: {e}")
        raise

def populate_fund_types(cursor: sqlite3.Cursor, fund_type_mapping: Dict[str, str]) -> None:
    """Populate fund_type column for existing records."""
    print("Populating fund_type for existing records...")
    
    try:
        # Get all unique fund codes that don't have fund_type set
        cursor.execute("""
            SELECT DISTINCT code 
            FROM tefas_fund_info 
            WHERE fund_type IS NULL
        """)
        
        codes_without_type = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(codes_without_type)} fund codes without fund_type")
        
        updated_count = 0
        
        for code in codes_without_type:
            if code in fund_type_mapping:
                fund_type = fund_type_mapping[code]
                cursor.execute("""
                    UPDATE tefas_fund_info 
                    SET fund_type = ? 
                    WHERE code = ? AND fund_type IS NULL
                """, (fund_type, code))
                updated_count += 1
        
        print(f"✅ Updated {updated_count} records with fund_type")
        
        # For remaining records without fund_type, set to 'UNKNOWN'
        cursor.execute("""
            UPDATE tefas_fund_info 
            SET fund_type = 'UNKNOWN' 
            WHERE fund_type IS NULL
        """)
        
        remaining_updated = cursor.rowcount
        if remaining_updated > 0:
            print(f"✅ Set {remaining_updated} records to fund_type 'UNKNOWN'")
        
    except sqlite3.Error as e:
        print(f"❌ Error populating fund types: {e}")
        raise

def verify_migration(cursor: sqlite3.Cursor) -> None:
    """Verify the migration was successful."""
    print("Verifying migration...")
    
    try:
        # Check column exists
        cursor.execute("PRAGMA table_info(tefas_fund_info)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fund_type' not in columns:
            print("❌ fund_type column not found!")
            return
        
        # Check fund_type distribution
        cursor.execute("""
            SELECT fund_type, COUNT(*) as count 
            FROM tefas_fund_info 
            GROUP BY fund_type 
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        print("Fund type distribution:")
        for fund_type, count in results:
            print(f"  {fund_type}: {count} records")
        
        # Check for NULL values
        cursor.execute("SELECT COUNT(*) FROM tefas_fund_info WHERE fund_type IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"⚠️  Warning: {null_count} records still have NULL fund_type")
        else:
            print("✅ All records have fund_type set")
        
    except sqlite3.Error as e:
        print(f"❌ Error verifying migration: {e}")
        raise

def main():
    """Run the migration."""
    print("🚀 Starting fund_type migration...")
    
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Step 1: Add fund_type column
            add_fund_type_column(cursor)
            
            # Step 2: Create index
            create_fund_type_index(cursor)
            
            # Step 3: Build fund type mapping
            fund_type_mapping = get_fund_type_mapping(cursor)
            
            # Step 4: Populate fund types
            populate_fund_types(cursor, fund_type_mapping)
            
            # Step 5: Verify migration
            verify_migration(cursor)
            
            conn.commit()
            print("✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
