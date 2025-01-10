import requests
import json
from web3 import Web3
from eth_abi.codec import ABICodec
from eth_abi.registry import registry

class LogProcessor:
    def __init__(self, etherscan_api_key):
        """
        Initialize the log processor with required configurations.

        Args:
            etherscan_api_key (str): API key for fetching ABIs from Etherscan.
        """
        self.etherscan_api_key = etherscan_api_key
        self.abi_cache = {}  # Cache for storing ABIs by contract address
        self.known_events = {}  # Global mapping of event signatures to definitions
        self.web3 = Web3()  # Web3 instance for hash and address decoding
        self.abi_codec = ABICodec(registry)  # ABI codec for decoding logs

    def fetch_abi(self, contract_address):
        """
        Fetch the ABI for a given contract address, with caching.

        Args:
            contract_address (str): The Ethereum contract address.

        Returns:
            list: The ABI of the contract if found, otherwise None.
        """
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
            if data.get("status") == "1":
                abi = json.loads(data["result"])
                self.abi_cache[contract_address] = abi
                return abi

        return None

    def map_event_signatures(self, abi):
        """
        Map event signatures from a contract's ABI to their definitions.

        Args:
            abi (list): The ABI of the contract.

        Returns:
            dict: A mapping of event signature hashes to event definitions.
        """
        events = [item for item in abi if item["type"] == "event"]
        event_mapping = {}
        for event in events:
            signature = f"{event['name']}({','.join([i['type'] for i in event['inputs']])})"
            hashed_signature = self.web3.keccak(text=signature).hex()
            event_mapping[hashed_signature] = event
            self.known_events[hashed_signature] = signature
        return event_mapping

    def decode_log(self, log, event_mapping):
        """
        Decode a log using the provided event mapping.

        Args:
            log (dict): The log to decode.
            event_mapping (dict): Mapping of event signatures to definitions.

        Returns:
            dict: Decoded log details or a placeholder for unknown events.
        """
        event_signature = log["topics"][0].hex()
        if event_signature in event_mapping:
            event = event_mapping[event_signature]
            indexed_inputs = [i for i in event["inputs"] if i["indexed"]]
            non_indexed_inputs = [i for i in event["inputs"] if not i["indexed"]]

            # Decode indexed parameters
            decoded_topics = [
                self.abi_codec.decode([i["type"]], bytes.fromhex(topic.hex()))[0]
                for topic, i in zip(log["topics"][1:], indexed_inputs)
            ]

            # Decode non-indexed parameters
            if non_indexed_inputs and log["data"] != "0x":
                decoded_data = self.abi_codec.decode(
                    [i["type"] for i in non_indexed_inputs],
                    bytes.fromhex(log["data"][2:])
                )
            else:
                decoded_data = []

            # Combine decoded parameters
            return {
                "event": event["name"],
                **{i["name"]: v for i, v in zip(indexed_inputs + non_indexed_inputs, decoded_topics + list(decoded_data))}
            }

        return {"event": "Unknown", "log": log}

    def summarize_transaction(self, transaction_hash, logs):
        """
        Summarize a transaction based on its logs.

        Args:
            transaction_hash (str): The transaction hash.
            logs (list): Decoded logs from the transaction.

        Returns:
            dict: A summary of the transaction.
        """
        summary = {"transactionHash": transaction_hash, "actions": []}
        for log in logs:
            action = {"contract": log.get("address", "Unknown"), "details": {}}
            if log["event"] == "Unknown":
                action["type"] = "Unknown Event"
                action["details"] = log.get("log", {})
            else:
                action["type"] = log["event"]
                action["details"] = {k: v for k, v in log.items() if k not in {"event", "log"}}
            summary["actions"].append(action)
        return summary

    def process_transaction_logs(self, transaction_logs):
        """
        Process and summarize logs for a set of transactions.

        Args:
            transaction_logs (dict): Logs grouped by transaction hash.

        Returns:
            list: Summarized transactions.
        """
        summarized_transactions = []

        for tx_hash, logs in transaction_logs.items():
            decoded_logs = []
            for log in logs:
                contract_address = log["address"]
                abi = self.fetch_abi(contract_address)

                if abi:
                    event_mapping = self.map_event_signatures(abi)
                    decoded_logs.append(self.decode_log(log, event_mapping))
                else:
                    decoded_logs.append({"event": "Unknown", "log": log})

            summarized_transactions.append(self.summarize_transaction(tx_hash, decoded_logs))

        return summarized_transactions