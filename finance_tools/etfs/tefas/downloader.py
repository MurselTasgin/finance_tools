from .crawler import Crawler
import pandas as pd
import datetime

class TefasDownloader:
    def __init__(self):
        self.crawler = Crawler()

    def download_fund_prices(self, funds, startDate, endDate, columns=None, kind='YAT'):
        """
        Download fund prices from TEFAS.
        
        Args:
            funds: Fund name(s) - can be string or list of strings
            startDate: Start date in YYYY-MM-DD format
            endDate: End date in YYYY-MM-DD format
            columns: List of columns to return (optional)
            kind: Type of the fund. One of `YAT`, `EMK`, or `BYF`. Defaults to `YAT`. (optional)
                - `YAT`: Securities Mutual Funds
                - `EMK`: Pension Funds
                - `BYF`: Exchange Traded Funds
        
        Returns:
            pandas.DataFrame with fund data
        """
        f_list = []
        
        # Convert string dates to datetime objects
        if isinstance(startDate, str):
            startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
        if isinstance(endDate, str):
            endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")
        
        # Convert single fund name to list for consistent handling
        if isinstance(funds, str):
            funds = [funds]
        
        # Ensure endDate is not before startDate
        if endDate < startDate:
            raise ValueError("endDate cannot be before startDate")
        
        current_date = startDate
        
        while current_date <= endDate:
            # Determine chunk size based on whether we're fetching all funds or specific funds
            if funds is None:
                # For all funds, use shorter periods (5 days) to prevent timeouts
                chunk_size = 5
                print(f"Fetching ALL funds - using {chunk_size}-day chunks to prevent timeouts")
            else:
                # For specific funds, use longer periods (30 days) for efficiency
                chunk_size = 30
                print(f"Fetching specific funds - using {chunk_size}-day chunks")
            
            # Calculate the end date for this chunk
            chunk_end = min(current_date + datetime.timedelta(days=chunk_size), endDate)
            
            b_date = current_date.strftime("%Y-%m-%d")
            e_date = chunk_end.strftime("%Y-%m-%d")
            
            print(f"Fetching data from {b_date} to {e_date}")
            
            if funds is not None:
                for f_name in funds:
                    try:
                        t_data = self.crawler.fetch(
                            start=b_date, 
                            end=e_date, 
                            name=f_name,
                            columns=columns, 
                            kind=kind
                        )
                        if not t_data.empty:
                            f_list.append(t_data)
                            print(f"  ✅ Fetched data for {f_name}: {len(t_data)} rows")
                        else:
                            print(f"  ⚠️  No data found for {f_name}")
                    except Exception as e:
                        print(f"  ❌ Error fetching data for {f_name}: {e}")
            else:
                try:
                    t_data = self.crawler.fetch(
                        start=b_date, 
                        end=e_date,
                        name=None, 
                        columns=columns, 
                        kind=kind
                    )
                    if not t_data.empty:
                        f_list.append(t_data)
                        print(f"  ✅ Fetched data: {len(t_data)} rows")
                    else:
                        print(f"  ⚠️  No data found")
                except Exception as e:
                    print(f"  ❌ Error fetching data: {e}")
            
            # Move to next chunk
            current_date = chunk_end + datetime.timedelta(days=1)
            
            # Add a small delay when fetching all funds to prevent overwhelming the server
            if funds is None:
                import time
                time.sleep(1)  # 1 second delay between chunks for all funds
        
        # Combine all fetched data
        if f_list:
            funds_df = pd.concat(f_list, ignore_index=True)
            # Rename 'code' column to 'symbol' if it exists
            if 'code' in funds_df.columns:
                funds_df.rename(columns={"code": "symbol"}, inplace=True)
            return funds_df
        else:
            print("⚠️  No data was fetched. Returning empty DataFrame.")
            return pd.DataFrame()