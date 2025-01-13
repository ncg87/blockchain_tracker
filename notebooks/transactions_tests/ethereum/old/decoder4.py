import requests
import json
from web3 import Web3
from eth_abi.codec import ABICodec
from eth_abi.registry import registry
from concurrent.futures import ThreadPoolExecutor

abi_codec = ABICodec(registry)
web3 = Web3()

class LogDecoder:
    def __init__(self, etherscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.abi_cache = {}
        self.known_events = {}
        self.unknown_logs = []
        self._session = requests.Session()  # Reuse HTTP connection
        
    def fetch_abi_from_explorer(self, contract_address):
        if contract_address in self.abi_cache:
            return self.abi_cache[contract_address]

        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.etherscan_api_key
        }

        try:
            response = self._session.get("https://api.etherscan.io/api", params=params)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "1":
                    abi = json.loads(data["result"])
                    self.abi_cache[contract_address] = abi
                    return abi
        except Exception as e:
            print(f"ABI fetch error for {contract_address}: {e}")
        return None

    def get_event_signature_hash(self, event_abi):
        signature = event_abi["name"] + "(" + ",".join(i["type"] for i in event_abi["inputs"]) + ")"
        return Web3.keccak(text=signature).hex()

    def map_signatures_to_events(self, abi):
        events = {}
        for item in abi:
            if item["type"] == "event":
                signature = item["name"] + "(" + ",".join(input["type"] for input in item["inputs"]) + ")"
                hashed_signature = Web3.keccak(text=signature).hex()
                events[hashed_signature] = item
        return events

    def decode_log(self, log, event_abi):
        try:
            event_signature = self.get_event_signature_hash(event_abi)
            if event_signature not in self.known_events:
                self.known_events[event_signature] = (
                    event_abi["name"] + 
                    "(" + 
                    ",".join(i["type"] for i in event_abi["inputs"]) + 
                    ")"
                )

            # Fast path for no parameters
            if not event_abi["inputs"]:
                return {"event": event_abi["name"]}

            # Pre-allocate lists for better performance
            indexed_inputs = []
            non_indexed_inputs = []
            for input_param in event_abi["inputs"]:
                if input_param["indexed"]:
                    indexed_inputs.append(input_param)
                else:
                    non_indexed_inputs.append(input_param)

            decoded_topics = []
            topics = log["topics"][1:]  # Skip first topic (event signature)
            
            # Batch process topics
            for topic, input_param in zip(topics, indexed_inputs):
                try:
                    if input_param["type"] in ["bytes", "string"]:
                        decoded_topics.append(topic.hex())
                    else:
                        decoded_value = abi_codec.decode(
                            [input_param["type"]], 
                            bytes.fromhex(topic.hex())
                        )[0]
                        decoded_topics.append(decoded_value)
                except Exception as e:
                    print(f"Topic decode error: {e}")
                    decoded_topics.append(None)

            # Process data field
            decoded_data = []
            if non_indexed_inputs and log["data"] != "0x":
                types = [i["type"] for i in non_indexed_inputs]
                try:
                    decoded_data = list(abi_codec.decode(
                        types, 
                        bytes.fromhex(log["data"].hex())
                    ))
                except Exception as e:
                    print(f"Data decode error: {e}")

            # Construct result directly
            result = {"event": event_abi["name"]}
            
            # Add decoded topics
            for input_param, value in zip(indexed_inputs, decoded_topics):
                result[input_param["name"]] = value
                
            # Add decoded data
            for input_param, value in zip(non_indexed_inputs, decoded_data):
                result[input_param["name"]] = value

            return result

        except Exception as e:
            print(f"Log decode error: {e}")
            return None

    def decode_batch(self, logs_chunk):
        decoded = {}
        for log in logs_chunk:
            tx_hash = log["transactionHash"].to_0x_hex()
            if tx_hash not in decoded:
                decoded[tx_hash] = []
                
            contract_address = log["address"]
            if not contract_address or not log.get("topics"):
                self.unknown_logs.append(log)
                continue

            abi = self.abi_cache.get(contract_address) or self.fetch_abi_from_explorer(contract_address)
            if not abi:
                continue
                
            signature_to_event = self.map_signatures_to_events(abi)
            event_signature = log["topics"][0].hex()
            
            if event_signature in signature_to_event:
                decoded_log = self.decode_log(log, signature_to_event[event_signature])
                if decoded_log:
                    decoded_log["contract"] = contract_address
                    decoded[tx_hash].append(decoded_log)
                    continue

            decoded_log = self.decode_log_without_abi(log)
            decoded_log["contract"] = contract_address
            decoded[tx_hash].append(decoded_log)
            
        return decoded

    def process_transaction_logs(self, logs, batch_size=100, max_workers=4):
        # Split logs into batches for parallel processing
        batches = [logs[i:i + batch_size] for i in range(0, len(logs), batch_size)]
        
        # Process batches in parallel
        decoded_transactions = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.decode_batch, batches))
            
        # Merge results
        for result in results:
            for tx_hash, decoded_logs in result.items():
                if tx_hash not in decoded_transactions:
                    decoded_transactions[tx_hash] = []
                decoded_transactions[tx_hash].extend(decoded_logs)
                
        return decoded_transactions

    def decode_log_without_abi(self, log):
        if not log.get("topics"):
            return {"event": "Unknown", "log": log}

        event_signature = log["topics"][0].hex()
        if event_signature in self.known_events:
            signature = self.known_events[event_signature]
            inputs = signature[signature.index("(") + 1:-1].split(",")
            
            # Pre-allocate result list
            result_values = []
            
            # Process topics
            topics = log["topics"][1:]
            for topic, input_type in zip(topics, inputs[:len(topics)]):
                topic_hex = topic.hex()
                if input_type == "address":
                    result_values.append("0x" + topic_hex[-40:])
                elif input_type == "uint256":
                    result_values.append(int(topic_hex, 16))
                else:
                    result_values.append(topic_hex)

            # Process data if needed
            if len(inputs) > len(result_values):
                data_types = inputs[len(result_values):]
                try:
                    decoded_data = abi_codec.decode(
                        data_types, 
                        bytes.fromhex(log["data"].hex())
                    )
                    result_values.extend(decoded_data)
                except Exception:
                    pass

            # Construct result
            result = {
                "event": signature[:signature.index("(")],
            }
            
            # Add parameters
            for i, value in enumerate(result_values, 1):
                result[f"param{i}"] = value

            return result

        return {"event": "Unknown", "log": log}