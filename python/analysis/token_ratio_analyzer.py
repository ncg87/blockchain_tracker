import pandas as pd
import numpy as np
from typing import Optional, Union
from datetime import datetime
from database.operator import DatabaseOperator
from decimal import Decimal

class TokenRatioAnalyzer:
    def __init__(self, db_operator: DatabaseOperator):
        """Initialize the analyzer with database operator"""
        self.db = db_operator
        
        # Default block times in seconds for different chains
        self.chain_block_times = {
            'ethereum': 12,
            'polygon': 2,
            'arbitrum': 1,
            'optimism': 2,
            'base': 2,
            'bnb': 3,
            'avalanche': 2,
            'polygonzk': 2,
            'zksync': 1,
            'mantle': 2,
            'linea': 2
        }

    def fetch_swap_data(self,
                       chain: str = 'ethereum',
                       factory_address: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch swap data with detailed token information"""
        query = """
            SELECT 
                timestamp,
                factory_address,
                contract_address,
                ABS(amount0) as amount0,
                ABS(amount1) as amount1,
                token0_address,
                token1_address,
                token0_name,
                token1_name,
                token0_symbol,
                token1_symbol,
                name as pool_name,
                log_index
            FROM evm_swaps
            WHERE chain = %(chain)s
            AND amount0 != 0 
            AND amount1 != 0
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
        
        # Execute query and create DataFrame
        with self.db.sql.db.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            
        if df.empty:
            return pd.DataFrame()
            
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        return df

    def create_token_ratio_matrix(self,
                                df: pd.DataFrame,
                                time_interval: Optional[int] = None,
                                chain: str = 'ethereum',
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                min_swaps: Optional[int] = None) -> pd.DataFrame:
        """
        Create a multi-level indexed DataFrame of token ratios
        
        Parameters:
        - df: Input DataFrame with swap data
        - time_interval: Interval in seconds between data points
        - chain: Blockchain name for default block time
        - start_date: Start datetime for analysis
        - end_date: End datetime for analysis
        - min_swaps: Minimum number of swaps required for a token pair to be included
        """
        if df.empty:
            return pd.DataFrame()
            
        # Use chain's block time if interval not specified
        if time_interval is None:
            time_interval = self.chain_block_times.get(chain, 12)
            
        # Convert datetime objects to Unix timestamps if provided
        start_timestamp = int(start_date.timestamp()) if start_date else df['timestamp'].min()
        end_timestamp = int(end_date.timestamp()) if end_date else df['timestamp'].max()
        
        # Create timestamp range based on the interval
        timestamps = np.arange(
            start_timestamp,
            end_timestamp + time_interval,
            time_interval
        )
        
        # Calculate price ratios for both directions
        df['ratio_0_1'] = df['amount0'] / df['amount1']
        df['ratio_1_0'] = df['amount1'] / df['amount0']
        
        # Create token pair identifiers
        df['token_pair_0_1'] = (
            df['token0_symbol'].fillna(df['token0_address']) + 
            '/' + 
            df['token1_symbol'].fillna(df['token1_address'])
        )
        df['token_pair_1_0'] = (
            df['token1_symbol'].fillna(df['token1_address']) + 
            '/' + 
            df['token0_symbol'].fillna(df['token0_address'])
        )
        
        # If min_swaps is specified, filter out pairs with insufficient swaps
        if min_swaps is not None:
            # Count swaps for each pair in both directions
            swaps_0_1 = df.groupby(['factory_address', 'token_pair_0_1']).size()
            swaps_1_0 = df.groupby(['factory_address', 'token_pair_1_0']).size()
            
            # Get pairs that meet the threshold
            valid_pairs_0_1 = swaps_0_1[swaps_0_1 >= min_swaps].index
            valid_pairs_1_0 = swaps_1_0[swaps_1_0 >= min_swaps].index
            
            # Filter dataframe to only include pairs with enough swaps
            mask_0_1 = df.set_index(['factory_address', 'token_pair_0_1']).index.isin(valid_pairs_0_1)
            mask_1_0 = df.set_index(['factory_address', 'token_pair_1_0']).index.isin(valid_pairs_1_0)
            df = df[mask_0_1 | mask_1_0].copy()
            
            if df.empty:
                print(f"No token pairs found with at least {min_swaps} swaps")
                return pd.DataFrame()
        
        # Process ratios for both directions, handling duplicates by taking highest log_index
        def process_direction(direction_df, pair_col, ratio_col):
            # Discretize timestamps into intervals
            direction_df['interval_timestamp'] = (
                (direction_df['timestamp'] // time_interval) * time_interval
            )
            
            return (direction_df
                .sort_values('log_index', ascending=False)
                .groupby(['factory_address', pair_col, 'interval_timestamp'])[ratio_col]
                .first()
                .unstack(level=2)
            )
        
        # Process 0->1 ratios
        ratio_df_0_1 = process_direction(
            df.copy(),
            'token_pair_0_1',
            'ratio_0_1'
        )
        
        # Process 1->0 ratios
        ratio_df_1_0 = process_direction(
            df.copy(),
            'token_pair_1_0',
            'ratio_1_0'
        )
        
        # Combine both directions
        result_df = pd.concat([ratio_df_0_1, ratio_df_1_0])
        
        # Ensure all timestamps in the range are present
        all_timestamps = pd.DataFrame(index=result_df.index, columns=timestamps)
        result_df = result_df.reindex(columns=all_timestamps.columns)
        
        # Forward fill missing values
        result_df = result_df.fillna(method='ffill', axis=1)
        
        # Add column names as datetime for better readability
        result_df.columns = pd.to_datetime(result_df.columns, unit='s')
        
        return result_df

    def analyze_token_ratios(self,
                           chain: str = 'ethereum',
                           factory_address: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           time_interval: Optional[int] = None,
                           min_swaps: Optional[int] = None) -> pd.DataFrame:
        """
        Complete analysis pipeline for token ratios
        
        Parameters:
        - chain: Blockchain to analyze
        - factory_address: Optional factory address to filter by
        - start_date: Start datetime for analysis
        - end_date: End datetime for analysis
        - time_interval: Interval in seconds between data points
        - min_swaps: Minimum number of swaps required for a token pair to be included
        """
        
        print("Fetching swap data...")
        df = self.fetch_swap_data(
            chain=chain,
            factory_address=factory_address,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            print("No swap data found for the specified parameters")
            return pd.DataFrame()
            
        print(f"Found {len(df)} swaps")
        print(f"Time range: {pd.to_datetime(df['timestamp'].min(), unit='s')} to {pd.to_datetime(df['timestamp'].max(), unit='s')}")
        print(f"Number of unique factories: {df['factory_address'].nunique()}")
        print(f"Number of unique pools: {df['contract_address'].nunique()}")
        
        print("Creating token ratio matrix...")
        result_df = self.create_token_ratio_matrix(
            df,
            time_interval=time_interval,
            chain=chain,
            start_date=start_date,
            end_date=end_date,
            min_swaps=min_swaps
        )
        
        if not result_df.empty:
            print(f"Final number of token pairs: {len(result_df)}")
        
        print("Analysis complete!")
        return result_df

    def get_token_ratios(self,
                        df: pd.DataFrame,
                        factory_address: Optional[str] = None,
                        token_symbol: Optional[str] = None,
                        token_address: Optional[str] = None) -> pd.DataFrame:
        """
        Extract specific token ratios from the analyzed DataFrame
        
        Parameters:
        - df: Analyzed DataFrame from analyze_token_ratios
        - factory_address: Optional factory address to filter by
        - token_symbol: Token symbol to search for
        - token_address: Token address to search for
        
        Returns:
        - DataFrame with matching token ratios
        """
        if df.empty:
            return pd.DataFrame()
            
        # Filter by factory if specified
        if factory_address:
            df = df.xs(factory_address, level='factory_address', drop_level=False)
            
        # Filter by token symbol or address
        if token_symbol or token_address:
            search_term = token_symbol or token_address
            mask = df.index.get_level_values(1).str.contains(search_term, case=False)
            df = df[mask]
            
        return df 