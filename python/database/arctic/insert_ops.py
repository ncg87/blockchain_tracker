from typing import List, Dict, Any
from .base import ArcticDB
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class ArcticInsertOperations:
    """
    ArcticDB Insert Operations.
    """
    def __init__(self, db: ArcticDB):
        self.db = db

    async def swaps(self, records: List[Dict]):
        """
        Insert swap data into ArcticDB optimized for high-frequency Uniswap V2 pool updates.
        """
        try:
            # Convert records to DataFrame
            df = pd.DataFrame(records)
            
            # Add timestamp index
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('datetime', inplace=True)
            
            # Pre-sort the entire dataset by datetime
            df = df.sort_index()
            
            # Replace None values with NaN
            df = df.replace({None: np.nan})
            
            # Create compound key using contract_address instead of factory_id
            df['pool_key'] = df['chain'] + '_' + df['contract_address'] + '_' + df['from_coin_address'] + '_' + df['to_coin_address']
            grouped = df.groupby('pool_key')
            
            lib = self.db.get_library('dex_swaps')
            
            # Process each pool's updates
            for pool_key, group_df in grouped:
                # Drop the temporary pool_key column
                group_df = group_df.drop('pool_key', axis=1)
                
                # Append to Arctic using the pool key as symbol
                symbol = f"swaps_{pool_key}"
                try:
                    lib.append(symbol, group_df)
                except Exception as e:
                    # Handle case where symbol doesn't exist yet
                    lib.write(symbol, group_df)
                    logger.info(f"Created new symbol {symbol}")
            
            logger.info(f"Inserted {len(df)} swap records across {len(grouped)} pools into ArcticDB")
            return True
        except Exception as e:
            logger.error(f"Error inserting swaps into ArcticDB: {e}")
            return False

    def insert_market_data(self, market_data: pd.DataFrame, symbol: str) -> bool:
        """
        Insert market data into ArcticDB.
        """
        try:
            lib = self.db.get_library('market_data')
            lib.write(symbol, market_data, dynamic_strings=True)
            logger.info(f"Inserted market data for {symbol} into ArcticDB.")
            return True
        except Exception as e:
            logger.error(f"Error inserting market data: {e}")
            return False
