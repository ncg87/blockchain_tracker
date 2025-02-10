import os
import dotenv

dotenv.load_dotenv()

class Settings:
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
    BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY')
    BASESCAN_API_KEY = os.getenv('BASESCAN_API_KEY')
    ARBISCAN_API_KEY = os.getenv('ARBISCAN_API_KEY')
    SNOWSCAN_API_KEY = os.getenv('SNOWSCAN_API_KEY')
    OPTIMISTIC_ETHERSCAN_API_KEY = os.getenv('OPTIMISTIC_ETHERSCAN_API_KEY')
    POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY')
    ZKSYNC_API_KEY = os.getenv('ZKSYNC_API_KEY')
    MANTLESCAN_API_KEY = os.getenv('MANTLESCAN_API_KEY')
    POLYGONZKSCAN_API_KEY = os.getenv('POLYGONZKSCAN_API_KEY')
    LINEASCAN_API_KEY = os.getenv('LINEASCAN_API_KEY')

    ETHEREUM_ENDPOINT = os.getenv('ETHEREUM_ENDPOINT')
    ETHEREUM_WEBSOCKET_ENDPOINT = os.getenv('ETHEREUM_WEBSOCKET_ENDPOINT')
    
    SOLANA_ENDPOINT = os.getenv('SOLANA_ENDPOINT')
    SOLANA_WEBSOCKET_ENDPOINT = os.getenv('SOLANA_WEBSOCKET_ENDPOINT')
    
    XRP_ENDPOINT = os.getenv('XRP_ENDPOINT')
    XRP_WEBSOCKET_ENDPOINT = os.getenv('XRP_WEBSOCKET_ENDPOINT')
    
    BITCOIN_ENDPOINT = os.getenv('BITCOIN_ENDPOINT')
    BITCOIN_WEBSOCKET_ENDPOINT = os.getenv('BITCOIN_WEBSOCKET_ENDPOINT')
    
    BNB_ENDPOINT = os.getenv('BNB_ENDPOINT')
    BNB_WEBSOCKET_ENDPOINT = os.getenv('BNB_WEBSOCKET_ENDPOINT')
    
    BASE_ENDPOINT = os.getenv('BASE_ENDPOINT')
    BASE_WEBSOCKET_ENDPOINT = os.getenv('BASE_WEBSOCKET_ENDPOINT')
    
    ARBITRUM_ENDPOINT = os.getenv('ARBITRUM_ENDPOINT')
    ARBITRUM_WEBSOCKET_ENDPOINT = os.getenv('ARBITRUM_WEBSOCKET_ENDPOINT')
    
    AVALANCHE_ENDPOINT = os.getenv('AVALANCHE_ENDPOINT')
    AVALANCHE_WEBSOCKET_ENDPOINT = os.getenv('AVALANCHE_WEBSOCKET_ENDPOINT')
    
    OPTIMISM_ENDPOINT = os.getenv('OPTIMISM_ENDPOINT')
    OPTIMISM_WEBSOCKET_ENDPOINT = os.getenv('OPTIMISM_WEBSOCKET_ENDPOINT')
    
    POLYGON_ENDPOINT = os.getenv('POLYGON_ENDPOINT')
    POLYGON_WEBSOCKET_ENDPOINT = os.getenv('POLYGON_WEBSOCKET_ENDPOINT')
    
    POLYGONZK_ENDPOINT = os.getenv('POLYGONZK_ENDPOINT')
    POLYGONZK_WEBSOCKET_ENDPOINT = os.getenv('POLYGONZK_WEBSOCKET_ENDPOINT')
    
    ZKSYNC_ENDPOINT = os.getenv('ZKSYNC_ENDPOINT')
    ZKSYNC_WEBSOCKET_ENDPOINT = os.getenv('ZKSYNC_WEBSOCKET_ENDPOINT')
    
    MANTLE_ENDPOINT = os.getenv('MANTLE_ENDPOINT')
    MANTLE_WEBSOCKET_ENDPOINT = os.getenv('MANTLE_WEBSOCKET_ENDPOINT')
    
    LINEA_ENDPOINT = os.getenv('LINEA_ENDPOINT')
    LINEA_WEBSOCKET_ENDPOINT = os.getenv('LINEA_WEBSOCKET_ENDPOINT')
    
    # MONGO CONFIG
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    


    # POSTGRES CONFIG
    POSTGRES_CONFIG = {
        "dbname": os.getenv('DB_NAME'),
        "user": os.getenv('DB_USER'),
        "password": os.getenv('DB_PASSWORD'),
        "host": os.getenv('DB_HOST'),
        "port": int(os.getenv('DB_PORT')) if os.getenv('DB_PORT') else 5432,
    }
    
    # NEO4J CONFIG
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_DB_NAME = os.getenv('NEO4J_DB_NAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

    # CLICKHOUSE CONFIG
    CLICKHOUSE_CONFIG = {
        "host": os.getenv('CLICKHOUSE_HOST', 'localhost'),
        "port": int(os.getenv('CLICKHOUSE_PORT', 9000)),
        "database": os.getenv('CLICKHOUSE_DB', 'blockchain_db'),
        "user": os.getenv('CLICKHOUSE_USER', 'default'),
        "password": os.getenv('CLICKHOUSE_PASSWORD', ''),
        "settings": {
            "use_numpy": True
        }
    }

    # ARCTICDB CONFIG
    ARCTICDB_CONFIG = {
        "host": os.getenv('ARCTICDB_HOST', 'localhost'),
        "database": os.getenv('ARCTICDB_DB', 'blockchain_db'),
        "lib_options": {
            "dynamic_strings": True,
            "force_strings": True
        }
    }



