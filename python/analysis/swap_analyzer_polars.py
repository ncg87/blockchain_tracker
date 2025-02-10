import polars as pl
from datetime import datetime
from typing import Optional, Union
import pyarrow as pa
from database.operator import DatabaseOperator
from decimal import Decimal

class SwapAnalyzerPolars:
    def __init__(self, db_operator: DatabaseOperator):
        """Initialize the analyzer with database operator"""
        self.db = db_operator
        
    def fetch_swap_data(self,
                       chain: str = 'ethereum',
                       factory_address: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pl.DataFrame:
        """Fetch swap data from database with optional date and factory filtering"""
        query = """
            SELECT 
                es.contract_address,
                es.timestamp,
                ABS(es.amount0) as abs_amount0,
                ABS(es.amount1) as abs_amount1,
                es.token0_symbol,
                es.token1_symbol,
                es.factory_address,
                es.name as pool_name,
                si.name as factory_name
            FROM evm_swaps es
            LEFT JOIN evm_contract_to_factory si 
                ON es.factory_address = si.factory_address 
                AND es.chain = si.chain
            WHERE es.chain = %(chain)s
        """
        
        params = {'chain': chain}
        
        if factory_address:
            query += " AND es.factory_address = %(factory_address)s"
            params['factory_address'] = factory_address
        
        if start_date:
            query += " AND es.timestamp >= %(start_timestamp)s"
            params['start_timestamp'] = int(start_date.timestamp())
        
        if end_date:
            query += " AND es.timestamp <= %(end_timestamp)s"
            params['end_timestamp'] = int(end_date.timestamp())
            
        query += " ORDER BY es.timestamp ASC"
        
        # Use the database operator to execute the query
        with self.db.sql.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                return pl.DataFrame()
                
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
            
            # Create Polars DataFrame with proper column names
            df = pl.DataFrame(
                {col: [row[i] for row in processed_results] for i, col in enumerate(columns)}
            )
            
            # Ensure proper types
            df = df.with_columns([
                pl.col('timestamp').cast(pl.Int64),
                pl.col('abs_amount0').cast(pl.Float64),
                pl.col('abs_amount1').cast(pl.Float64)
            ])
            
        return df

    def create_price_ratio_matrix(self,
                                df: pl.DataFrame,
                                resample_freq: str = '1s') -> pl.DataFrame:
        """Create a matrix of price ratios with contracts as columns and timestamps as index"""
        
        # Check if DataFrame is empty
        if df.is_empty():
            print("No swap data found for the specified parameters")
            return pl.DataFrame()
        
        # Filter out rows where amount1 is 0 and convert timestamp to datetime
        df = (
            df.filter(pl.col('abs_amount1') != 0)
            .with_columns([
                pl.col('timestamp').map(lambda x: datetime.fromtimestamp(x)).alias('datetime'),
                (pl.col('abs_amount0') / pl.col('abs_amount1')).alias('price_ratio')
            ])
            # Filter out infinite values
            .filter(
                ~pl.col('price_ratio').is_infinite()
            )
        )
        
        # Check if we still have data after filtering
        if df.height == 0:
            print("No valid price ratios found after filtering")
            return pl.DataFrame()
        
        # Get min and max timestamps
        min_time = df.select(pl.col('datetime').min()).item()
        max_time = df.select(pl.col('datetime').max()).item()
        
        # Create complete timestamp range
        date_range = pl.date_range(
            min_time,
            max_time,
            interval=resample_freq,
            eager=True
        ).alias('datetime')
        
        # Process each contract
        unique_contracts = df.select('contract_address').unique()
        contract_dfs = []
        
        for contract in unique_contracts.iter_rows():
            contract = contract[0]
            
            # Filter data for this contract and handle duplicates
            contract_data = (
                df.filter(pl.col('contract_address') == contract)
                .groupby('datetime')
                .agg([
                    pl.col('price_ratio').mean().alias('price_ratio')
                ])
                .sort('datetime')
            )
            
            # Join with complete date range and forward fill
            filled_data = (
                pl.DataFrame({'datetime': date_range})
                .join(contract_data, on='datetime', how='left')
                .with_columns([
                    pl.col('price_ratio').forward_fill(),
                    pl.lit(contract).alias('contract_address')
                ])
            )
            
            contract_dfs.append(filled_data)
        
        # Combine all contracts
        if not contract_dfs:
            return pl.DataFrame()
        
        result_df = pl.concat(contract_dfs)
        
        # Pivot to get contracts as columns
        result_df = result_df.pivot(
            values='price_ratio',
            index='datetime',
            columns='contract_address'
        ).sort('datetime')
        
        return result_df

    def analyze_swaps(self,
                     chain: str = 'ethereum',
                     factory_address: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     resample_freq: str = '1s') -> pl.DataFrame:
        """Complete analysis pipeline"""
        
        # Fetch data
        df = self.fetch_swap_data(
            chain=chain,
            factory_address=factory_address,
            start_date=start_date,
            end_date=end_date
        )
        
        # Print some information about the data
        if not df.is_empty():
            print(f"Found {df.height} swaps")
            print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"Number of unique contracts: {df['contract_address'].n_unique()}")
        else:
            print(f"No swaps found for factory {factory_address} in date range")
        
        # Create price ratio matrix
        result_df = self.create_price_ratio_matrix(df, resample_freq)
        
        return result_df
    
    def save_analysis(self,
                     df: pl.DataFrame,
                     filepath: str,
                     format: str = 'parquet') -> None:
        """Save analysis results to file"""
        if format == 'parquet':
            df.write_parquet(filepath)
        elif format == 'csv':
            df.write_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_factory_data(self, df: pl.DataFrame, factory_address: str) -> pl.DataFrame:
        """Extract data for a specific factory"""
        if df.is_empty():
            return pl.DataFrame()
            
        return df.filter(pl.col('factory_address') == factory_address) 