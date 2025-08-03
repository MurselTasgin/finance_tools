
from finance_tools.stocks.data_downloaders import YFinanceDownloader  as yf_tool

data_downloader = yf_tool()
# stock_data = data_downloader.execute(symbols=["AAPL", "MSFT"], start_date="2024-01-01", end_date="2024-12-31", period="1y", interval="1d")

# print(stock_data)

stock_data2 = data_downloader._download_single_stock(symbol="AAPL", 
                                                     start_date="2024-01-01", 
                                                     end_date="2024-12-31", 
                                                     period="1y", 
                                                     interval="1d",
                                                     include_dividends=True,
                                                     include_splits=True,
                                                     auto_adjust=True)
print(stock_data2)


stock_data3 = data_downloader._download_multiple_stocks(symbols=["AAPL", "MSFT"], 
                                                     start_date="2024-01-01", 
                                                     end_date="2024-12-31", 
                                                     period="1y", 
                                                     interval="1d",
                                                     include_dividends=True,
                                                     include_splits=True,
                                                     auto_adjust=True)
print(stock_data3['data'])
print(stock_data3['data'])