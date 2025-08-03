#!/usr/bin/env python3
"""
Example showing both dictionary and attribute access patterns for download results.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
from finance_tools.utils.simple_result import SimpleResult, create_download_result
import pandas as pd

def demonstrate_access_patterns():
    """Demonstrate both access patterns."""
    print("Demonstrating Access Patterns for Download Results")
    print("=" * 50)
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    try:
        # Download data
        result = downloader.execute(
            symbols=["AAPL"],
            period="1mo",
            interval="1d",
            return_format="dataframe"
        )
        
        print("✅ Download successful!")
        print()
        
        # Method 1: Using the existing ToolResult (attribute access)
        print("1. Using ToolResult (attribute access):")
        print(f"   result.data type: {type(result.data)}")
        print(f"   result.success: {result.success}")
        print(f"   result.error: {result.error}")
        
        if hasattr(result.data, 'data'):
            df = result.data['data']
            print(f"   DataFrame shape: {df.shape}")
            print(f"   DataFrame columns: {list(df.columns)}")
        print()
        
        # Method 2: Convert to SimpleResult for both access patterns
        print("2. Converting to SimpleResult (both access patterns):")
        
        # Create SimpleResult from the download result
        simple_result = SimpleResult({
            'data': result.data,
            'success': result.success,
            'error': result.error,
            'metadata': result.metadata,
            'execution_time': result.execution_time
        })
        
        # Dictionary access
        print("   Dictionary access:")
        print(f"   simple_result['data'] type: {type(simple_result['data'])}")
        print(f"   simple_result['success']: {simple_result['success']}")
        
        # Attribute access
        print("   Attribute access:")
        print(f"   simple_result.data type: {type(simple_result.data)}")
        print(f"   simple_result.success: {simple_result.success}")
        
        # Both work the same way
        print("   Both access patterns work identically!")
        print(f"   simple_result['data'] == simple_result.data: {simple_result['data'] == simple_result.data}")
        print()
        
        # Method 3: Using the helper function
        print("3. Using helper function:")
        helper_result = create_download_result(
            data=result.data,
            success=result.success,
            error=result.error,
            metadata=result.metadata,
            execution_time=result.execution_time
        )
        
        print(f"   helper_result['data'] type: {type(helper_result['data'])}")
        print(f"   helper_result.data type: {type(helper_result.data)}")
        print()
        
        # Demonstrate accessing the actual DataFrame
        print("4. Accessing the DataFrame:")
        if isinstance(result.data, dict) and 'data' in result.data:
            df = result.data['data']
            print(f"   DataFrame shape: {df.shape}")
            print(f"   First few rows:")
            print(df.head(3))
            print()
            
            # You can also access it via the SimpleResult
            simple_df = simple_result.data['data']
            print(f"   Same DataFrame via SimpleResult: {simple_df.shape}")
            print(f"   Dataframes are identical: {df.equals(simple_df)}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def show_simple_usage():
    """Show simple usage examples."""
    print("\n" + "=" * 50)
    print("Simple Usage Examples")
    print("=" * 50)
    
    # Example 1: Direct usage
    print("Example 1: Direct usage with both access patterns")
    result_dict = {'data': pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}), 'success': True}
    result = SimpleResult(result_dict)
    
    print(f"   result['data']: {type(result['data'])}")
    print(f"   result.data: {type(result.data)}")
    print(f"   Both access patterns work: {result['data'].equals(result.data)}")
    print()
    
    # Example 2: Using helper function
    print("Example 2: Using helper function")
    helper_result = create_download_result(
        data=pd.DataFrame({'X': [10, 20], 'Y': [30, 40]}),
        success=True,
        error=None,
        metadata={'source': 'example'}
    )
    
    print(f"   helper_result['data']: {type(helper_result['data'])}")
    print(f"   helper_result.data: {type(helper_result.data)}")
    print(f"   helper_result.success: {helper_result.success}")
    print(f"   helper_result.metadata: {helper_result.metadata}")

if __name__ == "__main__":
    demonstrate_access_patterns()
    show_simple_usage() 