from typing import List, Dict, Any, Optional
from .base import ArcticDB
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class ArcticQueryOperations:
    """
    ArcticDB Query Operations using the new arcticdb package.
    """
    def __init__(self, db: ArcticDB):
        self.db = db

    def query_recent_swaps(self, limit: int = 10) -> Optional[pd.DataFrame]:
        """
        Query recent swap transactions.
        :param limit: Number of most recent records to return
        :return: DataFrame containing swap data or None if error occurs
        """
        try:
            lib = self.db.get_library('dex_swaps')
            # Get all symbols and sort them by timestamp (they're in the format 'swaps_timestamp')
            symbols = sorted(lib.list_symbols(), reverse=True)
            
            if not symbols:
                logger.info("No swap data found in the database")
                return None
            
            # Read the most recent dataset
            latest_symbol = symbols[0]
            df = lib.read(latest_symbol)
            
            # Sort by timestamp if available and return the most recent records
            if not df.empty and 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            return df.head(limit)
        except Exception as e:
            logger.error(f"Error querying recent swaps: {e}")
            return None

    def query_market_data(self, 
                         symbol: str, 
                         start_date: Optional[pd.Timestamp] = None,
                         end_date: Optional[pd.Timestamp] = None) -> Optional[pd.DataFrame]:
        """
        Query market data for a specific symbol.
        :param symbol: The market symbol to query
        :param start_date: Optional start date filter
        :param end_date: Optional end date filter
        :return: DataFrame containing market data or None if error occurs
        """
        try:
            lib = self.db.get_library('market_data')
            data = lib.read(symbol)
            
            if data is None or data.empty:
                logger.info(f"No market data found for symbol: {symbol}")
                return None

            # Apply date filters if provided
            if start_date or end_date:
                mask = pd.Series(True, index=data.index)
                if start_date:
                    mask &= data.index >= start_date
                if end_date:
                    mask &= data.index <= end_date
                data = data[mask]

            return data
        except Exception as e:
            logger.error(f"Error querying market data for {symbol}: {e}")
            return None

    def get_available_symbols(self, library: str) -> List[str]:
        """
        Get list of available symbols in a library.
        :param library: Name of the library
        :return: List of available symbols
        """
        try:
            lib = self.db.get_library(library)
            return lib.list_symbols()
        except Exception as e:
            logger.error(f"Error getting symbols from library {library}: {e}")
            return []
