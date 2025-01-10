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
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
