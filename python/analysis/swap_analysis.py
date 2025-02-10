import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime
from database.operator import DatabaseOperator
from decimal import Decimal

# Fee mapping based on factory addresses
FEE_MAP = {
    '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f': 0.003,  # Uniswap V2
    '0x1F98431c8aD98523631AE4a59f267346ea31F984': 0.003,  # Uniswap V3 default
    # ... add other factory addresses and their fees
}

class DexAnalyzer:
    def __init__(self, db_operator: DatabaseOperator):
        """Initialize the analyzer with database operator"""
        self.db = db_operator
        
    def fetch_dex_data(self,
                      chain: str = 'ethereum',
                      factory_addresses: Optional[List[str]] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      min_swaps: int = 1000) -> pd.DataFrame:
        """
        Fetch DEX data combining swaps and syncs, filtered by factory activity
        """
        # First get active factories if not specified
        if not factory_addresses:
            factory_query = """
                SELECT factory_address, COUNT(*) as swap_count
                FROM evm_swaps
                WHERE chain = %(chain)s
                GROUP BY factory_address
                HAVING COUNT(*) >= %(min_swaps)s
            """
            with self.db.sql.db.get_connection() as conn:
                factory_df = pd.read_sql(factory_query, conn, params={
                    'chain': chain,
                    'min_swaps': min_swaps
                })
            factory_addresses = factory_df['factory_address'].tolist()
            
        if not factory_addresses:
            return pd.DataFrame()
            
        # Main query combining swaps and syncs
        query = """
            WITH ranked_swaps AS (
                SELECT 
                    s.*
                FROM evm_swaps s
                WHERE s.chain = %(chain)s
                AND s.factory_address = ANY(%(factory_addresses)s)
                AND ABS(s.amount1) > 0  -- Filter out zero amount1 values
            ),
            ranked_syncs AS (
                SELECT 
                    sync.*,
                    ROW_NUMBER() OVER (PARTITION BY sync.contract_address, sync.timestamp ORDER BY sync.log_index DESC) as rn
                FROM evm_syncs sync
                WHERE sync.chain = %(chain)s
                AND sync.contract_address IN (
                    SELECT DISTINCT contract_address 
                    FROM ranked_swaps
                )
            )
            SELECT 
                s.contract_address as "ContractID",
                s.factory_address as "FactoryID",
                s.timestamp as "Timestamp",
                s.token0_symbol as "FromCoin",
                s.token1_symbol as "ToCoin",
                sync.reserve0 as "ReserveFrom",
                sync.reserve1 as "ReserveTo",
                NULL as "PriceFromTo",
                s.token0_address as "FromCoinAddress",
                s.token1_address as "ToCoinAddress"
            FROM ranked_swaps s
            LEFT JOIN ranked_syncs sync 
                ON s.contract_address = sync.contract_address 
                AND s.timestamp = sync.timestamp
                AND sync.rn = 1
        """
        
        params = {
            'chain': chain,
            'factory_addresses': factory_addresses
        }
        
        if start_date:
            query = query.replace(
                "WHERE s.chain = %(chain)s",
                "WHERE s.chain = %(chain)s AND s.timestamp >= %(start_timestamp)s"
            )
            params['start_timestamp'] = int(start_date.timestamp())
        
        if end_date:
            query = query.replace(
                "WHERE s.chain = %(chain)s",
                "WHERE s.chain = %(chain)s AND s.timestamp <= %(end_timestamp)s"
            )
            params['end_timestamp'] = int(end_date.timestamp())
            
        query += " ORDER BY s.timestamp ASC"
            
        # Execute query and return DataFrame
        with self.db.sql.db.get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if df.empty:
            return df

        # Add hardcoded fee of 0.003
        df['Fee'] = 0.003
        
        # Convert reserves to float but keep NULL values as NaN
        df['ReserveFrom'] = pd.to_numeric(df['ReserveFrom'], errors='coerce')
        df['ReserveTo'] = pd.to_numeric(df['ReserveTo'], errors='coerce')

        # Create reverse entries
        reverse_df = df.copy()
        reverse_df['FromCoin'], reverse_df['ToCoin'] = df['ToCoin'], df['FromCoin']
        reverse_df['FromCoinAddress'], reverse_df['ToCoinAddress'] = df['ToCoinAddress'], df['FromCoinAddress']
        reverse_df['ReserveFrom'], reverse_df['ReserveTo'] = df['ReserveTo'], df['ReserveFrom']
        
        # Combine original and reverse entries
        df = pd.concat([df, reverse_df], ignore_index=True)
        
        # Sort by timestamp and contract to ensure proper forward filling
        df = df.sort_values(['Timestamp', 'ContractID', 'FromCoin', 'ToCoin'])
        
        # Get unique timestamps and contract combinations
        timestamps = df['Timestamp'].unique()
        contract_combos = df[['ContractID', 'FromCoin', 'ToCoin']].drop_duplicates()
        
        # Create a DataFrame with all combinations
        all_times = pd.DataFrame({'Timestamp': timestamps})
        all_combos = pd.merge(
            all_times, 
            contract_combos,
            how='cross'
        )
        
        # Merge with original data
        df = pd.merge(
            all_combos,
            df,
            on=['Timestamp', 'ContractID', 'FromCoin', 'ToCoin'],
            how='left'
        )
        
        # Forward fill within groups
        df = df.sort_values(['Timestamp', 'ContractID', 'FromCoin', 'ToCoin'])
        fill_columns = ['FactoryID', 'ReserveFrom', 'ReserveTo', 'FromCoinAddress', 'ToCoinAddress', 'Fee']
        df[fill_columns] = df.groupby(['ContractID', 'FromCoin', 'ToCoin'])[fill_columns].ffill()
        
        # Calculate prices where we have both reserves
        mask = df['ReserveFrom'].notna() & df['ReserveTo'].notna()
        df.loc[mask, 'PriceFromTo'] = df[mask].apply(
            lambda row: self.price_from_to(
                float(row['Fee']), 
                float(row['ReserveFrom']), 
                float(row['ReserveTo'])
            ), axis=1
        )

        return df.sort_values(['Timestamp', 'ContractID', 'FromCoin', 'ToCoin'])
        
    def save_analysis(self, 
                     df: pd.DataFrame, 
                     filepath: str,
                     format: str = 'csv') -> None:
        """Save analysis results to file"""
        if format == 'parquet':
            df.to_parquet(filepath)
        elif format == 'csv':
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
    def price_from_to(self, fee: float, reserve_from: float, reserve_to: float) -> float:
        return  - np.log(reserve_from * (1 - fee) / reserve_to)
    

    def price_to_from(self, fee: float, reserve_from: float, reserve_to: float) -> float:
        return  - np.log(reserve_to * (1 - fee) / reserve_from)
    
