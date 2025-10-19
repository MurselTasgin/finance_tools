#!/usr/bin/env python3
"""
Script to migrate to unified download history tables.
This will:
1. Add new columns to download_history table (data_type, symbols, items_completed, items_failed)
2. Migrate data from stock_download_history to download_history
3. Drop old stock download tables
"""

import os
from pathlib import Path
import sqlite3

# Set database path
parent_dir = Path(__file__).parent
db_path = os.path.join(parent_dir, "test_finance_tools.db")

def migrate():
    """Perform migration."""
    print("=" * 70)
    print("Migrating to Unified Download History Tables")
    print("=" * 70)
    print(f"\nDatabase: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: Check if new columns exist
        cursor.execute("PRAGMA table_info(download_history)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✓ Current download_history columns: {', '.join(columns)}\n")
        
        # Step 2: Add new columns if they don't exist
        new_columns = [
            ("data_type", "VARCHAR(20) DEFAULT 'tefas'"),
            ("symbols", "JSON"),
            ("items_completed", "INTEGER DEFAULT 0"),
            ("items_failed", "INTEGER DEFAULT 0"),
        ]
        
        for col_name, col_def in new_columns:
            if col_name not in columns:
                print(f"⚙  Adding column: {col_name}")
                try:
                    cursor.execute(f"ALTER TABLE download_history ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"   ✓ Added {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print(f"   ✓ Column {col_name} already exists")
                    else:
                        raise
            else:
                print(f"✓ Column {col_name} already exists")
        
        # Step 3: Check if download_progress_log needs item_name column
        cursor.execute("PRAGMA table_info(download_progress_log)")
        log_columns = [row[1] for row in cursor.fetchall()]
        
        if "item_name" not in log_columns and "fund_name" in log_columns:
            print("\n⚙  Renaming fund_name to item_name in download_progress_log")
            # SQLite doesn't support RENAME COLUMN directly in older versions
            # We'll add item_name and copy data
            try:
                cursor.execute("ALTER TABLE download_progress_log ADD COLUMN item_name VARCHAR(100)")
                cursor.execute("UPDATE download_progress_log SET item_name = fund_name")
                conn.commit()
                print("   ✓ Added item_name column and copied data")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("   ✓ item_name column already exists")
                else:
                    raise
        elif "item_name" in log_columns:
            print("\n✓ download_progress_log already has item_name column")
        
        # Step 4: Migrate data from stock_download_history if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_download_history'")
        if cursor.fetchone():
            print("\n⚙  Migrating data from stock_download_history to download_history")
            
            # Check how many records to migrate
            cursor.execute("SELECT COUNT(*) FROM stock_download_history")
            stock_count = cursor.fetchone()[0]
            print(f"   Found {stock_count} stock download records to migrate")
            
            if stock_count > 0:
                # Migrate records
                cursor.execute("""
                    INSERT INTO download_history (
                        task_id, data_type, start_date, end_date, kind,
                        funds, symbols, status, start_time, end_time,
                        records_downloaded, total_records, items_completed, items_failed,
                        error_message, created_at
                    )
                    SELECT 
                        task_id, 
                        'stock' as data_type,
                        start_date, 
                        end_date,
                        interval as kind,
                        NULL as funds,
                        symbols,
                        status,
                        start_time,
                        end_time,
                        records_downloaded,
                        total_records,
                        symbols_completed as items_completed,
                        symbols_failed as items_failed,
                        error_message,
                        created_at
                    FROM stock_download_history
                    WHERE task_id NOT IN (SELECT task_id FROM download_history)
                """)
                migrated = cursor.rowcount
                conn.commit()
                print(f"   ✓ Migrated {migrated} records")
        
        # Step 5: Migrate progress logs from stock_download_progress_log if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_download_progress_log'")
        if cursor.fetchone():
            print("\n⚙  Migrating progress logs from stock_download_progress_log")
            
            cursor.execute("SELECT COUNT(*) FROM stock_download_progress_log")
            log_count = cursor.fetchone()[0]
            print(f"   Found {log_count} stock progress log entries")
            
            if log_count > 0:
                cursor.execute("""
                    INSERT INTO download_progress_log (
                        task_id, timestamp, message, message_type, progress_percent,
                        chunk_number, records_count, item_name, created_at
                    )
                    SELECT 
                        task_id,
                        timestamp,
                        message,
                        message_type,
                        progress_percent,
                        symbol_number as chunk_number,
                        records_count,
                        symbol as item_name,
                        created_at
                    FROM stock_download_progress_log
                    WHERE id NOT IN (SELECT id FROM download_progress_log WHERE task_id IN (SELECT task_id FROM stock_download_progress_log))
                """)
                migrated_logs = cursor.rowcount
                conn.commit()
                print(f"   ✓ Migrated {migrated_logs} progress log entries")
        
        # Step 6: Display summary
        print("\n" + "=" * 70)
        print("Migration Summary")
        print("=" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM download_history WHERE data_type='tefas'")
        tefas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM download_history WHERE data_type='stock'")
        stock_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM download_progress_log")
        total_logs = cursor.fetchone()[0]
        
        print(f"\n✓ download_history table:")
        print(f"  - TEFAS downloads: {tefas_count}")
        print(f"  - Stock downloads: {stock_count}")
        print(f"  - Total: {tefas_count + stock_count}")
        
        print(f"\n✓ download_progress_log table:")
        print(f"  - Total entries: {total_logs}")
        
        print("\n✓ Schema updated successfully!")
        print("\nNote: Old stock_download_history and stock_download_progress_log tables")
        print("      are still present but can be dropped manually if desired.")
        print("\n" + "=" * 70)
        print("Migration Complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

