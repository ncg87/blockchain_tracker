import os
import dotenv

dotenv.load_dotenv()

class Settings:
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
    QUICKNODE_ENDPOINT = os.getenv('QUICKNODE_ENDPOINT')