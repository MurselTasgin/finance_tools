# Finance Tools

A comprehensive financial analysis and data collection toolkit for Python.

## Features

- **Stock Data Analysis**: Download and analyze stock data from Yahoo Finance
- **Technical Analysis**: Calculate various technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **Financial News**: Collect and analyze financial news from multiple sources
- **ETF Analysis**: Compare and analyze ETF performance and characteristics
- **Data Visualization**: Create charts and graphs for financial data
- **Modular Architecture**: Extensible design with plugin support

## Installation

### From PyPI (when published)
```bash
pip install finance-tools
```

### From source
```bash
git clone https://github.com/yourusername/finance_tools.git
cd finance_tools
pip install -e .
```

### Development installation
```bash
pip install -e ".[dev]"
```

## Quick Start

### Using the Python API

```python
from finance_tools.stocks.data_downloaders import YFinanceDownloader, TechnicalAnalysisDownloader

# Download stock data
downloader = YFinanceDownloader()
data = downloader.download_data("AAPL", period="1y")
print(data.head())

# Perform technical analysis
tech_analyzer = TechnicalAnalysisDownloader()
indicators = tech_analyzer.analyze_technical_indicators("AAPL", indicators=["RSI", "MACD"])
print(indicators.tail())
```

### Using the Command Line Interface

```bash
# Download stock data
finance-tools stock-data AAPL --period 1y --output aapl_data.csv

# Get financial news
finance-tools news AAPL --limit 10 --output aapl_news.json

# Perform technical analysis
finance-tools technical AAPL --indicators RSI,MACD,BB --output aapl_technical.csv
```

## Project Structure

```
finance_tools/
├── finance_tools/
│   ├── __init__.py
│   ├── cli.py
│   ├── stocks/
│   │   ├── __init__.py
│   │   ├── data_downloaders/
│   │   │   ├── __init__.py
│   │   │   ├── base_tool.py
│   │   │   ├── yfinance.py
│   │   │   ├── financial_news.py
│   │   │   └── technical_analysis.py
│   │   ├── analytics/
│   │   │   └── __init__.py
│   │   └── examples/
│   │       └── yfinance_example1.ipynb
│   └── etfs/
│       └── __init__.py
├── tests/
├── docs/
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
```

## Usage Examples

### Stock Data Analysis

```python
from finance_tools.stocks.data_downloaders import YFinanceDownloader

# Initialize downloader
downloader = YFinanceDownloader()

# Download historical data
data = downloader.download_data("AAPL", period="2y")

# Get company info
info = downloader.get_company_info("AAPL")

# Get real-time price
price = downloader.get_current_price("AAPL")
```

### Technical Analysis

```python
from finance_tools.stocks.data_downloaders import TechnicalAnalysisDownloader

# Initialize analyzer
analyzer = TechnicalAnalysisDownloader()

# Analyze multiple indicators
indicators = analyzer.analyze_technical_indicators(
    "AAPL", 
    indicators=["RSI", "MACD", "BB", "SMA", "EMA"],
    period="1y"
)

# Get specific indicator
rsi = analyzer.calculate_rsi("AAPL", period=14)
```

### Financial News

```python
from finance_tools.stocks.data_downloaders import FinancialNewsDownloader

# Initialize news downloader
news_downloader = FinancialNewsDownloader()

# Get news for a stock
news = news_downloader.get_news("AAPL", limit=20)

# Search for specific topics
search_news = news_downloader.search_news("earnings report", limit=10)
```

## Configuration

The package uses environment variables for configuration. Create a `.env` file in your project root:

```env
# API Keys (if needed)
YAHOO_FINANCE_API_KEY=your_api_key_here
NEWS_API_KEY=your_news_api_key_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=finance_tools.log

# Data storage
DATA_CACHE_DIR=./cache
DATA_EXPIRY_HOURS=24
```

## Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/finance_tools.git
cd finance_tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=finance_tools

# Run specific test file
pytest tests/test_yfinance.py
```

### Code formatting

```bash
# Format code with black
black finance_tools/

# Sort imports with isort
isort finance_tools/

# Type checking with mypy
mypy finance_tools/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Yahoo Finance](https://finance.yahoo.com/) for financial data
- [yfinance](https://github.com/ranaroussi/yfinance) library
- [pandas](https://pandas.pydata.org/) for data manipulation
- [matplotlib](https://matplotlib.org/) and [plotly](https://plotly.com/) for visualization

## Support

If you encounter any issues or have questions, please:

1. Check the [documentation](https://finance-tools.readthedocs.io/)
2. Search existing [issues](https://github.com/yourusername/finance_tools/issues)
3. Create a new issue with a detailed description

## Roadmap

- [ ] Add more technical indicators
- [ ] Implement portfolio analysis tools
- [ ] Add machine learning models for price prediction
- [ ] Create web dashboard
- [ ] Add support for cryptocurrency data
- [ ] Implement real-time data streaming
- [ ] Add backtesting framework



* USAGE
**** IMPORTANT -----
To run the following commands, you need to install finance_tools, under the main folder i.e. pip install -e . 
----> DOWNLOAD DATA =======================================================================
To download tefas fund data, you can use the following cli command.

= Download Investment funds data (YAT) for the given start & end dates:
- (cenv312) finance_tools> finance-tools tefas 2025-09-01 2025-10-31 --kind YAT --db ./test_finance_tools.db

= Download pension funds data (EMK) for the given start & end dates:
- (cenv312) finance_tools>  finance-tools tefas 2025-08-15 2025-08-31 --kind EMK --db ./test_finance_tools.db


---> ETF Analysis ==========================================================================
finance-tools etf-analyze --start 2024-01-01 --end 2025-01-01 --include EMEK --ema 20 50 --ema-cross 20 50 --macd 26 12 9 --db ./test_finance_tools.db

finance-tools etf-analyze --start 2024-01-01 --end 2025-01-01 --exclude EMEK --ema 20 50 --ema-cross 20 50 --macd 26 12 9 --db ./test_finance_tools.db

finance-tools etf-analyze --funds NNF YAC --start 2024-01-01 --end 2025-01-01 --db ./test_finance_tools.db

finance-tools etf-scan --start 2024-06-01 --end 2025-05-01 --ema-short 20 --ema-long 50 --macd 26 12 9 \
    --rsi 14 --rsi-lower 30 --rsi-upper 70 --db ./test_finance_tools.db

-----> ETF Scanner =========================================================================
--> FOR INVESTEMENT ETFS
(cenv312) finance_tools>  finance-tools etf-scan --start 2024-07-01 --end 2025-09-04 --exclude EMEKL  --ema-short 20 --ema-long 50 --macd 26 12 9 \
    --rsi 14 --rsi-lower 30 --rsi-upper 70 --db ./test_finance_tools.db > etf_scan_results_04_Sep_2025.md


---------------
START BACKEND -
---------------
(cenv312) > cd backend
/Users/murseltasgin/PROJECTS/finance_tools/backend
(cenv312) backend >  uvicorn main:app --reload --host 0.0.0.0 --port 8070 