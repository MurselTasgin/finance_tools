from finance_tools.etfs import TefasDownloader

tefas_downloader = TefasDownloader()

fund_type ="YAT"
start_date = "2025-06-20"
end_date = "2025-07-20"
fund_name = None

etf_data = tefas_downloader.download_fund_prices(funds=fund_name, startDate=start_date, endDate=end_date, columns=None, kind=fund_type)

print(etf_data)