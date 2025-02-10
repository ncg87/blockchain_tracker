from typing import List, Dict, Any, Optional, Union
from .base import ArcticDB
import logging
import pandas as pd
import numpy as np
from datetime import datetime

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

    def query_swaps_by_time(self, 
                           start_time: Optional[Union[int, datetime, pd.Timestamp]] = None,
                           end_time: Optional[Union[int, datetime, pd.Timestamp]] = None,
                           pool_address: Optional[str] = None,
                           chain: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Query swap data within a specific time range.
        
        Args:
            start_time: Start time (unix timestamp in seconds)
            end_time: End time (unix timestamp in seconds)
            pool_address: Optional pool contract address to filter by
            chain: Optional chain to filter by (e.g., 'ethereum')
            
        Returns:
            DataFrame containing swap data with unix timestamp index
        """
        try:
            lib = self.db.get_library('dex_swaps')
            symbols = lib.list_symbols()
            
            # Convert any datetime/timestamp inputs to unix timestamps
            if isinstance(start_time, datetime):
                start_time = int(start_time.timestamp())
            elif isinstance(start_time, pd.Timestamp):
                start_time = int(start_time.timestamp())
                
            if isinstance(end_time, datetime):
                end_time = int(end_time.timestamp())
            elif isinstance(end_time, pd.Timestamp):
                end_time = int(end_time.timestamp())

            # Filter symbols if chain or pool_address is specified
            if chain or pool_address:
                filtered_symbols = []
                for symbol in symbols:
                    if chain and chain not in symbol:
                        continue
                    if pool_address and pool_address not in symbol:
                        continue
                    filtered_symbols.append(symbol)
                symbols = filtered_symbols

            dfs = []
            for symbol in symbols:
                try:
                    df = lib.read(symbol)
                    if df is not None and not df.empty:
                        # Convert index to unix timestamps if it isn't already
                        if not np.issubdtype(df.index.dtype, np.integer):
                            df.index = df.index.astype(np.int64) // 10**9
                            
                        # Apply time filters
                        if start_time:
                            df = df[df.index >= start_time]
                        if end_time:
                            df = df[df.index <= end_time]
                        
                        if not df.empty:
                            dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error reading symbol {symbol}: {e}")
                    continue

            if not dfs:
                return None

            # Combine all dataframes and sort by timestamp
            result = pd.concat(dfs)
            return result.sort_index()

        except Exception as e:
            logger.error(f"Error querying swaps by time: {e}")
            return None

    def query_exact_timestamp(self, 
                            timestamp: Union[int, datetime, pd.Timestamp],
                            pool_address: Optional[str] = None,
                            chain: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Query swap data at an exact timestamp.
        
        Args:
            timestamp: The exact timestamp to query (unix timestamp in seconds)
            pool_address: Optional pool contract address to filter by
            chain: Optional chain to filter by
            
        Returns:
            DataFrame containing swap data with unix timestamp index
        """
        try:
            # Convert to unix timestamp if needed
            if isinstance(timestamp, datetime):
                ts = int(timestamp.timestamp())
            elif isinstance(timestamp, pd.Timestamp):
                ts = int(timestamp.timestamp())
            else:
                ts = int(timestamp)

            # Query a small window around the timestamp
            start_time = ts - 1  # 1 second before
            end_time = ts + 1    # 1 second after
            
            df = self.query_swaps_by_time(
                start_time=start_time,
                end_time=end_time,
                pool_address=pool_address,
                chain=chain
            )
            
            if df is None or df.empty:
                return None
                
            # Get the exact timestamp or nearest available
            exact_ts = df.index[df.index.get_indexer([ts], method='nearest')[0]]
            return df.loc[[exact_ts]]

        except Exception as e:
            logger.error(f"Error querying exact timestamp: {e}")
            return None

    def read_symbol(self, lib, symbol, date_range=None):
        try:
            # Get the versioned item
            data = lib.read(symbol, date_range=date_range)
            
            # Check if data exists and has content before accessing
            if data is not None and hasattr(data, 'data') and not data.data.empty:
                return data.data
            else:
                return None
            
        except Exception as e:
            print(f"Error reading symbol {symbol}: {str(e)}")
            return None
