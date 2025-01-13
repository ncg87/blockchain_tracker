import requests
import json
from web3 import Web3
from eth_abi.codec import ABICodec
from eth_abi.registry import registry

abi_codec = ABICodec(registry)

class LogDecoder3:
    def __init__(self, etherscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.abi_cache = {}
        self.known_events = {} 
        self.unknown_logs = []
        


    def fetch_abi_from_explorer(self, contract_address):
        if contract_address in self.abi_cache:
            return self.abi_cache[contract_address]

        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.etherscan_api_key
        }

        response = requests.get("https://api.etherscan.io/api", params=params)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "1":
                abi = json.loads(data["result"])
                self.abi_cache[contract_address] = abi
                return abi
        return None

    def get_event_signature_hash(self, event_abi):
        signature = event_abi["name"] + "(" + ",".join(i["type"] for i in event_abi["inputs"]) + ")"
        return Web3.keccak(text=signature).hex()

    def map_signatures_to_events(self, abi):
        events = [item for item in abi if item["type"] == "event"]
        signature_to_event = {}
        for event in events:
            signature = event["name"] + "(" + ",".join([input["type"] for input in event["inputs"]]) + ")"
            hashed_signature = Web3.keccak(text=signature).hex()
            signature_to_event[hashed_signature] = event
        return signature_to_event

    def decode_log(self, log, event_abi):
        try:
            # Add the event signature to the known events
            event_signature = self.get_event_signature_hash(event_abi)
            if event_signature not in self.known_events:
                signature = event_abi["name"] + "(" + ",".join(i["type"] for i in event_abi["inputs"]) + ")"
                self.known_events[event_signature] = signature

            # Decode indexed parameters from topics
            indexed_inputs = [i for i in event_abi["inputs"] if i["indexed"]]
            decoded_topics = []

            # Process each indexed parameter individually
            for topic, input_param in zip(log["topics"][1:], indexed_inputs):
                try:
                    if input_param["type"] in ["bytes", "string"]:
                        # Dynamic types are hashed, return the raw hash
                        decoded_value = topic.hex()
                    else:
                        # Decode static types
                        decoded_value = abi_codec.decode([input_param["type"]], bytes.fromhex(topic.hex()))[0]
                    decoded_topics.append(decoded_value)
                except Exception as e:
                    print(f"Error decoding topic {topic.hex()} for event {event_abi['name']}: {e}")
                    decoded_topics.append(f"Error: {str(e)}")  # Append the error for debugging


            # Decode non-indexed parameters from data
            non_indexed_inputs = [i for i in event_abi["inputs"] if not i["indexed"]]
            if non_indexed_inputs and log["data"] != "0x":
                types_list = [i["type"] for i in non_indexed_inputs]
                decoded_data = abi_codec.decode(types_list, bytes.fromhex(log["data"].hex()))
            else:
                decoded_data = []

            # Combine decoded parameters
            decoded_event = {
                i["name"]: value for i, value in zip(indexed_inputs + non_indexed_inputs, decoded_topics + list(decoded_data))
            }
            decoded_event["event"] = event_abi["name"]
            return decoded_event
        except Exception as e:
            print(f"Error decoding log {log} for event {event_abi['name']}: {e}")
            return None
        
    def process_transaction_logs(self, logs):
        decoded_transactions = {}
        
        # Group logs by transaction hash first
        for log in logs:
            log = dict(log)
            tx_hash = log.get("transactionHash").to_0x_hex()
            if tx_hash not in decoded_transactions:
                decoded_transactions[tx_hash] = []
                
            contract_address = log.get("address")
            if not contract_address:
                print(f"No contract address found for log: {log}")
                self.unknown_logs.append(log)
                continue

            if not log.get("topics"):
                print(f"No event signature found for log: {log}")
                self.unknown_logs.append(log)
                continue

            # Proceed with ABI fetching and decoding
            abi = self.fetch_abi_from_explorer(contract_address)
            if abi:
                signature_to_event = self.map_signatures_to_events(abi)
                event_signature = log["topics"][0].hex() if log["topics"] else None
                if event_signature in signature_to_event:
                    event_abi = signature_to_event[event_signature]
                    decoded_log = self.decode_log(log, event_abi)
                    if decoded_log:
                        decoded_log["contract"] = contract_address
                        decoded_transactions[tx_hash].append(decoded_log)
                        continue

            # Fallback: Decode without ABI using known events
            decoded_log = self.decode_log_without_abi(log)
            if decoded_log["event"] == "Unknown":
                # Further fallback: Attempt heuristic decoding
                #decoded_log = self.heuristic_decode_log(log)
                self.unknown_logs.append(log)

            decoded_log["contract"] = contract_address
            decoded_transactions[tx_hash].append(decoded_log)

        return decoded_transactions
        
    def decode_log_without_abi(self, log):
        event_signature = log.get("topics")
        if not event_signature:
            print(f"No event signature found for log: {log}")
            return {"event": "Unknown", "log": log}
        event_signature = event_signature[0].hex()
        # Check if the event signature is already known
        if event_signature in self.known_events:
            signature = self.known_events[event_signature]
            inputs = signature[signature.index("(") + 1:-1].split(",")
            indexed_values = []

            # Decode indexed topics
            for topic, input_type in zip(log["topics"][1:], inputs[:len(log["topics"]) - 1]):
                if input_type == "address":
                    value = "0x" + topic.hex()[-40:]
                elif input_type == "uint256":
                    value = int(topic.hex(), 16)
                else:
                    value = topic.hex()
                indexed_values.append(value)

            # Decode non-indexed data
            if len(inputs) > len(indexed_values):
                data_types = inputs[len(indexed_values):]
                decoded_data = abi_codec.decode(data_types, bytes.fromhex(log["data"].hex()))
            else:
                decoded_data = []

            # Combine decoded values
            decoded_event = {f"param{i+1}": val for i, val in enumerate(indexed_values + list(decoded_data))}
            decoded_event["event"] = signature.split("(")[0]
            return decoded_event

        # If unknown, store the log for further analysis
        return {"event": "Unknown", "log": log}
    
    def heuristic_decode_log(self, log):
        decoded_log = {"event": "HeuristicDecoded", "log": log}

        # Decode indexed topics
        decoded_log["topics"] = []
        for topic in log["topics"]:
            if len(topic.hex()) == 66:  # Likely 32 bytes
                try:
                    value = int(topic.hex(), 16)
                    decoded_log["topics"].append(value)
                except ValueError:
                    decoded_log["topics"].append(topic.hex())

        # Decode data into 32-byte chunks
        decoded_log["data"] = []
        if log["data"] and log["data"] != "0x":
            for i in range(0, len(log["data"]) - 2, 64):  # 32 bytes = 64 hex characters
                chunk = log["data"][i + 2 : i + 66]  # Skip "0x"
                try:
                    value = int(chunk, 16)
                    decoded_log["data"].append(value)
                except ValueError:
                    decoded_log["data"].append(chunk)

        return decoded_log
