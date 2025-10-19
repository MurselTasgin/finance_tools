from .crawler import Crawler
import pandas as pd
import datetime
from typing import Callable, Optional

class TefasDownloader:
    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        self.crawler = Crawler()
        self.progress_callback = progress_callback
        self.total_chunks = 0
        self.current_chunk = 0

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
        
        if kind is None:
            kind = 'YAT'


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
        
        # Calculate total chunks for progress tracking
        current_date = startDate
        temp_date = startDate
        self.total_chunks = 0
        while temp_date <= endDate:
            if funds is None:
                chunk_size = 5
            else:
                chunk_size = 30
            temp_date = min(temp_date + datetime.timedelta(days=chunk_size), endDate)
            temp_date = temp_date + datetime.timedelta(days=1)
            self.total_chunks += 1
        
        self.current_chunk = 0
        current_date = startDate
        
        while current_date <= endDate:
            # Determine chunk size based on whether we're fetching all funds or specific funds
            if funds is None:
                # For all funds, use shorter periods (5 days) to prevent timeouts
                chunk_size = 5
                status_msg = f"Fetching ALL funds - using {chunk_size}-day chunks to prevent timeouts"
            else:
                # For specific funds, use longer periods (30 days) for efficiency
                chunk_size = 30
                status_msg = f"Fetching specific funds - using {chunk_size}-day chunks"
            
            # Calculate the end date for this chunk
            chunk_end = min(current_date + datetime.timedelta(days=chunk_size), endDate)
            
            b_date = current_date.strftime("%Y-%m-%d")
            e_date = chunk_end.strftime("%Y-%m-%d")
            
            # Report progress
            self.current_chunk += 1
            # Calculate progress: reserve last 10% for database saving (0-90% for download)
            download_progress = int((self.current_chunk / self.total_chunks) * 90)
            
            if self.progress_callback:
                self.progress_callback(f"Fetching data from {b_date} to {e_date} [Total chunks: {self.total_chunks}]", download_progress, self.current_chunk)
            else:
                print(f"Fetching data from {b_date} to {e_date} ({download_progress}%)")
            
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
                            msg = f"  ✅ Fetched data for {f_name}: {len(t_data)} rows"
                            if self.progress_callback:
                                self.progress_callback(msg, download_progress, self.current_chunk)
                            else:
                                print(msg)
                        else:
                            msg = f"  ⚠️  No data found for {f_name}"
                            if self.progress_callback:
                                self.progress_callback(msg, download_progress, self.current_chunk)
                            else:
                                print(msg)
                    except Exception as e:
                        msg = f"  ❌ Error fetching data for {f_name}: {e}"
                        if self.progress_callback:
                            self.progress_callback(msg, download_progress, self.current_chunk)
                        else:
                            print(msg)
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
                        msg = f"  ✅ Fetched data: {len(t_data)} rows"
                        if self.progress_callback:
                            self.progress_callback(msg, download_progress, self.current_chunk)
                        else:
                            print(msg)
                    else:
                        msg = f"  ⚠️  No data found"
                        if self.progress_callback:
                            self.progress_callback(msg, download_progress, self.current_chunk)
                        else:
                            print(msg)
                except Exception as e:
                    msg = f"  ❌ Error fetching data: {e}"
                    if self.progress_callback:
                        self.progress_callback(msg, download_progress, self.current_chunk)
                    else:
                        print(msg)
            
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
            
            final_msg = f"✅ Download completed! Total records: {len(funds_df)}"
            if self.progress_callback:
                # Download phase complete at 90%, leaving 10% for database save
                self.progress_callback(final_msg, 90, self.total_chunks)
            else:
                print(final_msg)
            return funds_df
        else:
            final_msg = "⚠️  No data was fetched. Returning empty DataFrame."
            if self.progress_callback:
                self.progress_callback(final_msg, 90, self.total_chunks)
            else:
                print(final_msg)
            return pd.DataFrame()