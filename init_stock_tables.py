#!/usr/bin/env python3
# init_stock_tables.py
"""
Script to initialize stock database tables.
Run this to create missing stock tables in the database.
"""

import os
from pathlib import Path

# Set database path
parent_dir = Path(__file__).parent
os.environ["DATABASE_NAME"] = os.path.join(parent_dir, "test_finance_tools.db")

from finance_tools.etfs.tefas.repository import DatabaseEngineProvider
from finance_tools.logging import get_logger

logger = get_logger("init_db")

def main():
    """Initialize stock database tables."""
    logger.info("=" * 60)
    logger.info("Initializing Stock Database Tables")
    logger.info("=" * 60)
    
    # Create database provider
    db_provider = DatabaseEngineProvider()
    
    # Check current state
    logger.info(f"Database path: {os.environ['DATABASE_NAME']}")
    
    if db_provider.is_initialized():
        logger.info("✅ All tables already exist!")
    else:
        logger.info("📋 Some tables are missing. Creating them...")
        db_provider.ensure_initialized()
        logger.info("✅ Database tables created successfully!")
    
    # Verify tables
    from sqlalchemy import inspect
    engine = db_provider.get_engine()
    inspector = inspect(engine)
    
    logger.info("\n📊 Available tables:")
    for table_name in sorted(inspector.get_table_names()):
        logger.info(f"  ✓ {table_name}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Initialization Complete!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

