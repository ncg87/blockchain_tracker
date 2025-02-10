import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from database.operator import DatabaseOperator
from decimal import Decimal

class SwapAnalyzerPandas:
    def __init__(self, db_operator: DatabaseOperator):
        """Initialize the analyzer with database operator"""
        self.db = db_operator
        
    def fetch_swap_data(self, 
                       chain: str = 'ethereum',
                       factory_address: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch swap data from database with optional date and factory filtering"""
        query = """
            SELECT 
                contract_address,
                timestamp,
                ABS(amount0) as abs_amount0,
                ABS(amount1) as abs_amount1,
                token0_symbol,
                token1_symbol,
                factory_address,
                name as pool_name
            FROM evm_swaps
            WHERE chain = %(chain)s
        """
        
        params = {'chain': chain}
        
        if factory_address:
            query += " AND factory_address = %(factory_address)s"
            params['factory_address'] = factory_address
        
        if start_date:
            query += " AND timestamp >= %(start_timestamp)s"
            params['start_timestamp'] = int(start_date.timestamp())
        
        if end_date:
            query += " AND timestamp <= %(end_timestamp)s"
            params['end_timestamp'] = int(end_date.timestamp())
            
        query += " ORDER BY timestamp ASC"
        
        # Use the database operator to execute the query
        with self.db.sql.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                return pd.DataFrame()
                
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            
            # Convert Decimal values to float
            processed_results = []
            for row in results:
                processed_row = []
                for value in row:
                    if isinstance(value, Decimal):
                        processed_row.append(float(value))
                    else:
                        processed_row.append(value)
                processed_results.append(processed_row)
            
            # Create DataFrame with proper column names
            df = pd.DataFrame(processed_results, columns=columns)
            
            # Ensure proper types
            df['timestamp'] = df['timestamp'].astype('int64')
            df['abs_amount0'] = df['abs_amount0'].astype('float64')
            df['abs_amount1'] = df['abs_amount1'].astype('float64')
            
        return df

    def create_price_ratio_matrix(self, 
                                df: pd.DataFrame,
                                resample_freq: str = '1s') -> pd.DataFrame:
        """Create a matrix of price ratios with contracts as columns and timestamps as index"""
        
        # Check if DataFrame is empty
        if df.empty:
            print("No swap data found for the specified parameters")
            return pd.DataFrame()
        
        # Convert timestamp to datetime and set as index immediately
        df['datetime'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        
        # Calculate price ratio, filtering out rows where amount1 is 0
        df = df[df['abs_amount1'] != 0].copy()  # Filter out potential division by zero
        df['price_ratio'] = df['abs_amount0'] / df['abs_amount1']
        
        # Remove any infinite values that might occur
        df = df[~df['price_ratio'].isin([float('inf'), float('-inf')])]
        
        # Check if we still have data after filtering
        if len(df) == 0:
            print("No valid price ratios found after filtering")
            return pd.DataFrame()
        
        # Create full timestamp range
        full_range = pd.date_range(
            start=df['datetime'].min(),
            end=df['datetime'].max(),
            freq=resample_freq
        )
        
        # Process in chunks of contracts to avoid memory issues
        chunk_size = 100  # Adjust this based on your memory constraints
        unique_contracts = df['contract_address'].unique()
        result_dfs = []
        
        for i in range(0, len(unique_contracts), chunk_size):
            contract_chunk = unique_contracts[i:i + chunk_size]
            chunk_data = df[df['contract_address'].isin(contract_chunk)].copy()
            
            # Pivot the data directly
            pivoted = (chunk_data.pivot_table(
                index='datetime',
                columns='contract_address',
                values='price_ratio',
                aggfunc='mean'
            ).reindex(full_range))
            
            # Forward fill missing values
            pivoted = pivoted.ffill()
            
            result_dfs.append(pivoted)
            
            # Print progress
            print(f"Processed {min(i + chunk_size, len(unique_contracts))} out of {len(unique_contracts)} contracts")
        
        # Combine all chunks
        if result_dfs:
            result_df = pd.concat(result_dfs, axis=1)
        else:
            result_df = pd.DataFrame()
        
        return result_df
    
    def analyze_swaps(self,
                     chain: str = 'ethereum',
                     factory_address: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     resample_freq: str = '1s') -> pd.DataFrame:
        """Complete analysis pipeline"""
        
        # Fetch data
        print("Fetching swap data...")
        df = self.fetch_swap_data(
            chain=chain,
            factory_address=factory_address,
            start_date=start_date,
            end_date=end_date
        )
        
        # Print some information about the data
        if not df.empty:
            print(f"Found {len(df)} swaps")
            print(f"Time range: {pd.to_datetime(df['timestamp'].min(), unit='s')} to {pd.to_datetime(df['timestamp'].max(), unit='s')}")
            print(f"Number of unique contracts: {df['contract_address'].nunique()}")
        else:
            print(f"No swaps found for factory {factory_address} in date range")
            return pd.DataFrame()
        
        # Create price ratio matrix
        print("Creating price ratio matrix...")
        result_df = self.create_price_ratio_matrix(df, resample_freq)
        
        print("Analysis complete!")
        return result_df
    
    def save_analysis(self, 
                     df: pd.DataFrame, 
                     filepath: str,
                     format: str = 'parquet') -> None:
        """Save analysis results to file"""
        if format == 'parquet':
            df.to_parquet(filepath)
        elif format == 'csv':
            df.to_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}") 