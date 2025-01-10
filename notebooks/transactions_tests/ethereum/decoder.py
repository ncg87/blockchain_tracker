import requests
import json
from web3 import Web3
from eth_abi.codec import ABICodec
from eth_abi.registry import registry

abi_codec = ABICodec(registry)

class LogDecoder:
    def __init__(self, etherscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.abi_cache = {}
        self.known_events = {} 
        


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
            decoded_value = abi_codec.decode([input_param["type"]], bytes.fromhex(topic.hex()))[0]
            decoded_topics.append(decoded_value)

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

    def process_transaction_logs(self, transaction_logs):
        decoded_transactions = {}
        summarized_transactions = []
        unknown_logs = []  # To track logs that remain unknown

        for tx_hash, logs in transaction_logs.items():
            decoded_logs = []
            for log in logs:
                contract_address = log["address"]
                abi = self.fetch_abi_from_explorer(contract_address)

                if abi:
                    signature_to_event = self.map_signatures_to_events(abi)
                    event_signature = log["topics"][0].hex()
                    if event_signature in signature_to_event:
                        event_abi = signature_to_event[event_signature]
                        decoded_log = self.decode_log(log, event_abi)
                        decoded_logs.append(decoded_log)
                        continue

                # Fallback: Decode without ABI using known events
                decoded_log = self.decode_log_without_abi(log)
                if decoded_log["event"] == "Unknown":
                    # Further fallback: Attempt heuristic decoding
                    decoded_log = self.heuristic_decode_log(log)
                    unknown_logs.append(log)  # Track for logging statistics

                decoded_logs.append(decoded_log)

            # Summarize the transaction
            decoded_transactions[tx_hash] = decoded_logs
            transaction_summary = self.summarize_transaction(tx_hash, decoded_logs)
            summarized_transactions.append(transaction_summary)

        # Log statistics for unknown events
        self.log_unknown_events(unknown_logs)

        return summarized_transactions


    def summarize_transaction(self, transaction_hash, decoded_logs):
        """
        Summarizes the actions performed in a transaction based on decoded logs.

        Args:
            transaction_hash (str): The transaction hash.
            decoded_logs (list): A list of decoded logs for the transaction.

        Returns:
            dict: A summary of the transaction, including its actions and key details.
        """
        summary = {"transactionHash": transaction_hash, "actions": []}

        for log in decoded_logs:
            action = {"contract": log.get("log", {}).get("address", "Unknown"), "details": {}}
            
            if log["event"] == "Unknown":
                action["type"] = "Unknown Event"
                action["details"] = {"rawLog": log.get("log", {})}
            elif log["event"] == "HeuristicDecoded":
                action["type"] = "Heuristic Decoded Event"
                action["details"] = log.get("log", {})
            else:
                action["type"] = log["event"]
                action["details"] = {k: v for k, v in log.items() if k not in {"event", "log"}}
            
            summary["actions"].append(action)

        return summary

        
    def decode_log_without_abi(self, log):
        event_signature = log["topics"][0].hex()

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
    
    def log_unknown_events(self, logs):
        unknown_stats = {}
        for log in logs:
            contract = log["address"]
            event_signature = log["topics"][0].hex()
            key = (contract, event_signature)
            if key not in unknown_stats:
                unknown_stats[key] = 0
            unknown_stats[key] += 1

        # Print or store the statistics for later analysis
        for (contract, event_signature), count in unknown_stats.items():
            print(f"Contract: {contract}, Event: {event_signature}, Count: {count}")