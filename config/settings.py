import os
import dotenv

dotenv.load_dotenv()

class Settings:
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
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
