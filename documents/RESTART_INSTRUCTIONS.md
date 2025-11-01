# How to See Scanner Components in UI

## The Fix is Applied

The code has been fixed in `finance_tools/analytics/service.py` (lines 484-485).

## To See the Fix in Action

You need to:

1. **Stop the backend completely** (not just reload):
   ```bash
   pkill -f "uvicorn main:app"
   # OR
   pkill -f "python.*backend/main.py"
   ```

2. **Clear Python cache** (already done):
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

3. **Start backend fresh**:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8070 --reload
   ```

4. **Run a NEW ETF scan from the UI** - Old scans in database won't have the data, only new ones will.

## Verification

After running a new scan, check the database:
```bash
sqlite3 test_finance_tools.db "SELECT id, json_type(json_extract(results_data, '$.results[0].components')) as has_components FROM analysis_results WHERE analysis_type='etf_scan' ORDER BY id DESC LIMIT 1"
```

Should show: `<id>|object` (not empty/null)

## What You'll See

After running a new scan, the UI will display:
- **Score Contributions** column showing each scanner's weighted contribution
- **Technical Indicators** column showing current EMA, MACD, RSI values  
- **Detailed Reasons** with comprehensive analysis and emojis

Old scans in the database won't have this data - they'll show "No components data" and "No reasons data".

