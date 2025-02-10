from arcticdb import Arctic, LibraryOptions
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class ArcticDB:
    """
    ArcticDB Database class using the new arcticdb package.
    """
    def __init__(self, host=None, port=None, database="blockchain_data"):
        """
        Initialize ArcticDB connection.
        """
        try:
            self.host = host or Settings.ARCTICDB_HOST
            self.port = port or Settings.ARCTICDB_PORT
            self.database = database
            
            # Connect to ArcticDB using new syntax
            self.store = Arctic(f"lmdb:///{self.database}")
            
            # Initialize libraries if they don't exist
            self._initialize_libraries()
            
            logger.info(f"Connected to ArcticDB at {self.database}")
        except Exception as e:
            logger.error(f"Error connecting to ArcticDB: {e}")
            raise

    def _initialize_libraries(self):
        """
        Initialize required libraries in ArcticDB.
        """
        try:
            # Create libraries if they don't exist
            libraries = ['dex_swaps', 'market_data', 'blockchain_metrics']
            for lib in libraries:
                if lib not in self.store.list_libraries():
                    self.store.create_library(lib)
                    logger.info(f"Initialized library: {lib}")
        except Exception as e:
            logger.error(f"Error initializing libraries: {e}")
            raise

    def get_library(self, library_name: str):
        """
        Get a specific library from ArcticDB.
        """
        return self.store[library_name]

    def close(self):
        """
        Close the ArcticDB connection.
        """
        if hasattr(self, 'store'):
            self.store.close()
            logger.info("ArcticDB connection closed.")

    def __del__(self):
        """
        Ensure proper cleanup on object deletion.
        """
        self.close()
