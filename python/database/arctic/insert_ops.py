from typing import List, Dict, Any
from .base import ArcticDB
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class ArcticInsertOperations:
    """
    ArcticDB Insert Operations.
    """
    def __init__(self, db: ArcticDB):
        self.db = db

    def insert_swaps(self, swaps_df: pd.DataFrame, library: str = 'dex_swaps') -> bool:
        """
        Insert swap data into ArcticDB.
        :param swaps_df: DataFrame containing swap data
        :param library: Target library name
        """
        try:
            lib = self.db.get_library(library)
            # Use the timestamp as the key for versioning
            timestamp = pd.Timestamp.now()
            lib.write(f'swaps_{timestamp.timestamp()}', swaps_df, dynamic_strings=True)
            logger.info(f"Inserted {len(swaps_df)} swap records into ArcticDB.")
            return True
        except Exception as e:
            logger.error(f"Error inserting swaps: {e}")
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
