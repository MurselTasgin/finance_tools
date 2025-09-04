# finance_tools/etfs/analysis

Modular ETF analysis on TEFAS data retrieved from the local database via ORM.

Key components:
- `EtfDataRetriever`: reads `TefasFundInfo` via `TefasRepository` with keyword filters
- `TitleFilter`: dataframe-level include/exclude filters on `title`
- `TechnicalIndicatorCalculator`: EMA, RSI, MACD on any numeric column
- `EtfAnalyzer`: orchestrates the pipeline

Example usage:

```python
from datetime import date
from finance_tools.etfs.analysis import EtfAnalyzer, IndicatorRequest, KeywordFilter

analyzer = EtfAnalyzer()
request = IndicatorRequest(
    codes=["NNF", "YAC"],
    start=date(2024, 1, 1),
    end=date(2024, 3, 31),
    column="price",
    indicators={
        "ema": {"window": 20},
        "rsi": {"window": 14},
        "macd": {"window_slow": 26, "window_fast": 12, "window_sign": 9},
    },
    keyword_filter=KeywordFilter(include_keywords=["altin", "gold"], exclude_keywords=["usd"]),
)

results = analyzer.analyze(request)
for r in results:
    print(r.code)
    print(r.data.tail())
```


