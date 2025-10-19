#!/usr/bin/env python
"""
Script to create missing analysis tables in the database.
Run this to set up analysis_results and user_analysis_history tables.
"""

import sys
from finance_tools.etfs.tefas.repository import DatabaseEngineProvider
from finance_tools.logging import get_logger

logger = get_logger("migration")

def main():
    try:
        logger.info("Initializing database provider...")
        provider = DatabaseEngineProvider()
        
        logger.info("Checking database initialization status...")
        if provider.is_initialized():
            logger.info("All required tables already exist!")
            return 0
        
        logger.info("Creating missing tables...")
        provider.create_all()
        
        logger.info("Successfully created all missing tables!")
        return 0
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
