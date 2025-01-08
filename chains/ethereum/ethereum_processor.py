import logging
import json
from hexbytes import HexBytes
from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex, decode_extra_data

class EthereumProcessor(BaseProcessor):
    """
    Ethereum processor class.
    """
    def __init__(self, database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(database, 'Ethereum')
        self.querier = querier

    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['number']} on {self.network}")
        
        # Block specific data
        block_specific_data = {           
            "miner": block["miner"],
            "gas_limit": decode_hex(block["gasLimit"]),
            "extra_data": decode_extra_data(block),
            "gas_used": decode_hex(block["gasUsed"]),
            "base_fee": decode_hex(block["baseFeePerGas"]),
            "block_size": decode_hex(block["size"]),
            "blob_gas_used": decode_hex(block["blobGasUsed"]),
            "excess_blob_gas": decode_hex(block["excessBlobGas"]),
        } 
        
        block_data = {
            "network": self.network,
            "block_number": decode_hex(block["number"]),
            "block_hash": normalize_hex(block["hash"]),
            "parent_hash": normalize_hex(block["parentHash"]),
            "timestamp": decode_hex(block["timestamp"]),
            "block_data": json.dumps(block_specific_data) # Process this to JSON upon Postgres insertion
        }
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['number']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
        
        # Process withdrawals
        #self._process_withdrawals(block)
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
            
    def _process_transactions(self, block):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        self.logger.info(f"Processing transactions for block {block['number']}")
        for transaction in block['transactions']:
                    # Check if sender and recipient are contracts
            _ , to_is_contract = self.classify_transaction(transaction)

            # Get ABI for recipient (Going to figure out ABI and decoding issue later in the future)
            if False:
                decoded_input = self.decode_input_data(transaction['input'], transaction['to']) 
            else:
                decoded_input = None
            # Format transaction data
            transaction_data = {
                "network":  self.network,
                "block_number": transaction["blockNumber"],
                "transaction_hash": transaction["hash"].hex(),
                "from_address": transaction["from"],
                "to_address": transaction.get("to"),
                "amount": transaction.get("value"),
                "gas": transaction.get("gas"),
                "gas_price": transaction.get("gasPrice"),
                "input_data": transaction['input'].hex(),
                "timestamp": block["timestamp"],
            }
            # Store transaction data
            self.database.insert_transaction(transaction_data)
            self.logger.debug(f"Transaction {transaction['hash'].hex()} processed.")

    def _process_withdrawals(self, block):
        """
        Process raw withdrawal data and store it.
        """
        self.logger.info(f"Processing withdrawals for block {block['number']}")
        for withdrawl in block['withdrawals']:
            # Format withdrawal data
            withdrawal_data = {
                "network": self.network,
                "block_number": block["number"],
                "withdrawal_index": withdrawl["index"],
                "validator_index": withdrawl["validatorIndex"],
                "address": withdrawl["address"],
                "amount": withdrawl["amount"],
                "timestamp": block["timestamp"],
            }
            # Store withdrawal data
            self.database.insert_withdrawal(withdrawal_data)
            self.logger.debug(f"Withdrawal {withdrawal_data['withdrawal_index']} processed.")
    
    def classify_transaction(self, transaction):
        """
        Classify the sender and recipient of a transaction as wallet or contract.
        """
        sender_is_contract = self.querier.is_contract(transaction['from'])
        recipient_is_contract = self.querier.is_contract(transaction.get('to'))

        return sender_is_contract, recipient_is_contract
    
    def decode_input_data(self, input_data, address):
        """
        Decode transaction input data using ABI. Handles cases for unverified ABIs, proxy contracts, and missing data.
        """
        try:
            # Case for invalid input data
            if not input_data or input_data == "0x":
                self.logger.info(f"No input data to decode for address {address}")
                return None

            
            # Check if ABI is available in DB
            abi = self.database.query_contract_metadata(address)
            
            # If not, get it from Etherscan, and store it in DB
            if not abi:
                abi = self.querier.get_contract_abi(address)
                if abi:
                    self.database.insert_contract_metadata(address, self.network, abi)
                else:
                    # Log and return None for unverified contracts
                    self.logger.warning(f"Cannot decode input: ABI not found or unverified for address {address}")
                    return None

            # Handle proxy contracts
            proxy_abi = [{"constant": True, "inputs": [], "name": "implementation", "outputs": [{"name": "", "type": "address"}], "payable": False, "stateMutability": "view", "type": "function"}]
            contract = self.querier.w3.eth.contract(address=address, abi=proxy_abi)
            try:
                implementation_address = contract.functions.implementation().call()
                self.logger.info(f"Proxy detected at {address}, using implementation contract {implementation_address}")
                abi = self.database.query_contract_metadata(implementation_address)
                if not abi:
                    abi = self.querier.get_contract_abi(implementation_address)
                    if abi:
                        self.database.insert_contract_metadata(implementation_address, self.network, abi)
                    else:
                        self.logger.warning(f"Implementation contract {implementation_address} ABI not found")
                        return None
            except Exception:
                self.logger.info(f"No proxy implementation function found for {address}, proceeding with current ABI")

            # Decode input data
            decoded_input = self.querier.decode_input_data(input_data, address, abi)
            if decoded_input:
                return refactor_input_data(decoded_input)
            else:
                self.logger.error(f"Decoding failed for {address} with available ABI")
                return None
        except Exception as e:
            self.logger.error(f"Error decoding input data for {address}: {e}")
            return None


def make_serializable(value):
    """
    Recursively make values JSON serializable.
    """
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    elif isinstance(value, list):
        return [make_serializable(v) for v in value]
    elif isinstance(value, dict):
        return {k: make_serializable(v) for k, v in value.items()}
    else:
        return value

def refactor_input_data(input_data):
    """
    Refactor input data into a text format.
    """
    try:
        if isinstance(input_data, tuple):
            function_signature = str(input_data[0])
            parameters = input_data[1]

            # Convert parameters to serializable format
            serializable_parameters = make_serializable(parameters)

            # Serialize the data
            serialized_input = json.dumps({
                'function': function_signature,
                'parameters': serializable_parameters
            })
            return serialized_input
        else:
            # Return raw input if not a tuple
            return json.dumps(input_data)
    except Exception as e:
        logging.error(f"Failed to refactor input data: {e}")
        return None

