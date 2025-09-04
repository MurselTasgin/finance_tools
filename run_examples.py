#!/usr/bin/env python3
"""
Simple script to run the finance tools examples with proper imports.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Run the examples with proper imports."""
    try:
        # Import and run the examples
        from finance_tools.analysis.example_usage import run_all_examples
        
        print("🚀 Starting Finance Tools Analysis Examples...")
        print("=" * 60)
        
        # Run all examples
        executive_summary = run_all_examples()
        
        if executive_summary:
            print("\n✅ All examples completed successfully!")
            print(f"📊 Executive Summary generated with {len(executive_summary.get('stocks_analyzed', []))} stocks analyzed")
        else:
            print("\n❌ Some examples failed to complete")
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install pandas numpy yfinance")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 