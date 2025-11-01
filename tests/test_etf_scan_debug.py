# test_etf_scan_debug.py
"""
Test ETF scan to debug components storage issue.
"""
import os
import sys
from pathlib import Path

# Set up paths and database
parent_dir = Path(__file__).parent
os.environ["DATABASE_NAME"] = os.path.join(parent_dir, "test_finance_tools.db")

from finance_tools.analytics.service import AnalyticsService
from finance_tools.etfs.tefas.repository import DatabaseEngineProvider
from sqlalchemy.orm import Session

def test_etf_scan():
    """Test ETF scan with detailed logging."""
    print("=" * 80)
    print("Testing ETF Scan with Component Tracking")
    print("=" * 80)
    
    # Initialize service
    analytics_service = AnalyticsService()
    
    # Get database session
    engine_provider = DatabaseEngineProvider()
    session = Session(engine_provider.get_engine())
    
    try:
        # Run ETF scan with a few specific codes
        print("\n🔍 Running ETF scan analysis...")
        result = analytics_service.run_etf_scan_analysis(
            db_session=session,
            specific_codes=["AAK", "ABF", "ACF"],  # Test with 3 funds
            start_date="2024-01-01",
            end_date="2025-10-15",
            column="price",
            scanners=["ema_cross", "macd", "rsi"],
            scanner_configs={
                "ema_cross": {"short": 20, "long": 50},
                "macd": {"slow": 26, "fast": 12, "signal": 9},
                "rsi": {"window": 14}
            },
            weights={
                "w_ema": 1.0,
                "w_macd": 1.0,
                "w_rsi": 1.0
            },
            score_threshold=0.5,
            user_id="test_user",
            save_results=True
        )
        
        print("\n" + "=" * 80)
        print("Analysis Result Summary")
        print("=" * 80)
        print(f"Analysis Type: {result.get('analysis_type')}")
        print(f"Result Count: {result.get('result_count')}")
        print(f"Execution Time: {result.get('execution_time_ms')}ms")
        
        if 'results' in result and result['results']:
            print(f"\n📊 First Result Details:")
            first = result['results'][0]
            print(f"  Code: {first.get('code')}")
            print(f"  Recommendation: {first.get('recommendation')}")
            print(f"  Score: {first.get('score')}")
            
            print(f"\n  Components:")
            components = first.get('components', {})
            if components:
                for key, value in components.items():
                    print(f"    • {key}: {value}")
            else:
                print(f"    ❌ MISSING or EMPTY")
            
            print(f"\n  Indicators Snapshot:")
            indicators = first.get('indicators_snapshot', {})
            if indicators:
                for key, value in indicators.items():
                    print(f"    • {key}: {value}")
            else:
                print(f"    ❌ MISSING or EMPTY")
            
            print(f"\n  Reasons ({len(first.get('reasons', []))} items):")
            reasons = first.get('reasons', [])
            if reasons:
                for i, reason in enumerate(reasons[:5]):  # Show first 5
                    print(f"    {i+1}. {reason}")
                if len(reasons) > 5:
                    print(f"    ... and {len(reasons) - 5} more")
            else:
                print(f"    ❌ MISSING or EMPTY")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully")
        print("=" * 80)
        
        # Now check database
        print("\n🔍 Checking database storage...")
        from finance_tools.etfs.tefas.models import AnalysisResult
        
        db_result = session.query(AnalysisResult).filter_by(
            analysis_type='etf_scan'
        ).order_by(AnalysisResult.id.desc()).first()
        
        if db_result and db_result.results_data:
            print(f"✅ Found database record ID: {db_result.id}")
            results_data = db_result.results_data
            if 'results' in results_data and results_data['results']:
                first_db = results_data['results'][0]
                print(f"📊 First DB result for code: {first_db.get('code')}")
                print(f"  Has components: {'components' in first_db}")
                print(f"  Has indicators_snapshot: {'indicators_snapshot' in first_db}")
                print(f"  Has reasons: {'reasons' in first_db}")
                
                if 'components' in first_db:
                    print(f"  Components keys: {list(first_db['components'].keys())}")
                if 'indicators_snapshot' in first_db:
                    print(f"  Indicators keys: {list(first_db['indicators_snapshot'].keys())}")
                if 'reasons' in first_db:
                    print(f"  Reasons count: {len(first_db['reasons'])}")
        else:
            print("❌ No database record found")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    test_etf_scan()

