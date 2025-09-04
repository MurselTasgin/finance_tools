#!/usr/bin/env python3
"""
Data Organization Script for Finance Tools

This script helps organize downloaded data into a structured directory layout.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def create_data_structure():
    """Create organized data directory structure."""
    
    # Define data directories
    data_dirs = {
        "tefas": {
            "raw": "data/tefas/raw",
            "processed": "data/tefas/processed", 
            "exports": "data/tefas/exports"
        },
        "stocks": {
            "raw": "data/stocks/raw",
            "processed": "data/stocks/processed",
            "exports": "data/stocks/exports"
        },
        "news": {
            "raw": "data/news/raw",
            "processed": "data/news/processed"
        },
        "reports": "data/reports",
        "cache": "data/cache"
    }
    
    # Create directories
    for category, paths in data_dirs.items():
        if isinstance(paths, dict):
            for subdir in paths.values():
                Path(subdir).mkdir(parents=True, exist_ok=True)
                print(f"📁 Created: {subdir}")
        else:
            Path(paths).mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {paths}")
    
    # Create README files
    create_readme_files(data_dirs)
    
    print("\n✅ Data structure created successfully!")
    print("\n📋 Directory Structure:")
    print("data/")
    print("├── tefas/")
    print("│   ├── raw/          # Raw Tefas downloads")
    print("│   ├── processed/    # Cleaned/processed data")
    print("│   └── exports/      # Final exports")
    print("├── stocks/")
    print("│   ├── raw/          # Raw stock data")
    print("│   ├── processed/    # Processed stock data")
    print("│   └── exports/      # Final exports")
    print("├── news/")
    print("│   ├── raw/          # Raw news data")
    print("│   └── processed/    # Processed news data")
    print("├── reports/          # Generated reports")
    print("└── cache/            # Temporary cache files")

def create_readme_files(data_dirs):
    """Create README files for each directory."""
    
    readme_content = """# Data Directory

This directory contains financial data organized by type and processing stage.

## Directory Structure

- **raw/**: Original downloaded data files
- **processed/**: Cleaned and processed data
- **exports/**: Final formatted data for analysis

## File Naming Convention

- Tefas: `tefas_{type}_{funds}_{start_date}_{end_date}.csv`
- Stocks: `stocks_{symbols}_{period}_{date}.csv`
- News: `news_{symbol}_{date}_{limit}.json`

## Data Retention

- Raw data: Keep for 1 year
- Processed data: Keep for 6 months
- Exports: Keep for 3 months
- Cache: Clean weekly
"""
    
    # Create README for main data directory
    with open("data/README.md", "w") as f:
        f.write(readme_content)
    
    # Create README for each subdirectory
    for category, paths in data_dirs.items():
        if isinstance(paths, dict):
            for subdir in paths.values():
                readme_path = f"{subdir}/README.md"
                with open(readme_path, "w") as f:
                    f.write(f"# {subdir.split('/')[-1].title()} Data\n\n{readme_content}")

def organize_existing_files():
    """Organize existing downloaded files."""
    
    print("\n🔄 Organizing existing files...")
    
    # Find existing CSV files
    csv_files = list(Path(".").glob("tefas_*.csv"))
    
    if not csv_files:
        print("No existing Tefas CSV files found.")
        return
    
    # Create data directory if it doesn't exist
    Path("data/tefas/raw").mkdir(parents=True, exist_ok=True)
    
    # Move files
    for file_path in csv_files:
        new_path = f"data/tefas/raw/{file_path.name}"
        shutil.move(str(file_path), new_path)
        print(f"📁 Moved: {file_path.name} → {new_path}")

def get_data_paths():
    """Get standardized data paths."""
    return {
        "tefas_raw": "data/tefas/raw",
        "tefas_processed": "data/tefas/processed", 
        "tefas_exports": "data/tefas/exports",
        "stocks_raw": "data/stocks/raw",
        "stocks_processed": "data/stocks/processed",
        "stocks_exports": "data/stocks/exports",
        "news_raw": "data/news/raw",
        "news_processed": "data/news/processed",
        "reports": "data/reports",
        "cache": "data/cache"
    }

def generate_filename(data_type, **kwargs):
    """Generate standardized filename."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if data_type == "tefas":
        fund_type = kwargs.get("fund_type", "YAT")
        funds = kwargs.get("funds", "all")
        start_date = kwargs.get("start_date", "unknown")
        end_date = kwargs.get("end_date", "unknown")
        
        if isinstance(funds, list):
            funds = "_".join(funds)
        
        return f"tefas_{fund_type}_{funds}_{start_date}_{end_date}.csv"
    
    elif data_type == "stocks":
        symbols = kwargs.get("symbols", "unknown")
        period = kwargs.get("period", "unknown")
        
        if isinstance(symbols, list):
            symbols = "_".join(symbols)
        
        return f"stocks_{symbols}_{period}_{timestamp}.csv"
    
    elif data_type == "news":
        symbol = kwargs.get("symbol", "unknown")
        limit = kwargs.get("limit", "unknown")
        return f"news_{symbol}_{timestamp}_{limit}.json"
    
    else:
        return f"{data_type}_{timestamp}.csv"

if __name__ == "__main__":
    print("🗂️  Finance Tools Data Organization")
    print("=" * 50)
    
    # Create directory structure
    create_data_structure()
    
    # Organize existing files
    organize_existing_files()
    
    # Show usage examples
    print("\n📝 Usage Examples:")
    print("=" * 30)
    
    paths = get_data_paths()
    
    print(f"# Save Tefas data")
    print(f"data.to_csv('{paths['tefas_raw']}/tefas_YAT_NNF_2024-01-01_2024-12-31.csv')")
    
    print(f"\n# Save stock data") 
    print(f"data.to_csv('{paths['stocks_raw']}/stocks_AAPL_MSFT_1y_20241201_143022.csv')")
    
    print(f"\n# Save processed data")
    print(f"processed_data.to_csv('{paths['tefas_processed']}/tefas_processed_20241201.csv')")
    
    print(f"\n# Generate filename")
    print(f"filename = generate_filename('tefas', fund_type='BYF', funds='NNF', start_date='2024-01-01', end_date='2024-12-31')")
    print(f"# Result: tefas_BYF_NNF_2024-01-01_2024-12-31.csv")
