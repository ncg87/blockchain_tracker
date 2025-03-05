import requests
import json
from config import Settings
# Base chain RPC endpoint
RPC_URL = Settings.BASE_ENDPOINT

def get_latest_block():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(RPC_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        data = response.json()
        return int(data["result"], 16)  # Convert hex to integer
    return None

def get_pending_block():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["pending", True],
        "id": 1
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(RPC_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        data = response.json()
        if "result" in data and data["result"] is not None:
            return data["result"]
    return None

# Check if the pending block is truly pending
latest_block_number = get_latest_block()
pending_block = get_pending_block()

if pending_block:
    pending_block_number = pending_block["number"]
    if pending_block_number is None:
        print("✅ This is a true pending block. Transactions are still in the mempool.")
        print(json.dumps(pending_block["transactions"], indent=4))
    else:
        pending_block_number = int(pending_block_number, 16)
        print(f"🔍 Latest confirmed block: {latest_block_number}")
        print(f"📌 'Pending' block number: {pending_block_number}")

        if pending_block_number > latest_block_number:
            print("✅ This block is actually pending with transactions in the mempool.")
        else:
            print("⚠️ This is just the latest mined block, not actual pending transactions.")
else:
    print("❌ No pending transactions found.")
