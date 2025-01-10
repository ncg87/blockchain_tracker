import logging
import json
from hexbytes import HexBytes
from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex, decode_extra_data
from operator import itemgetter


# Item getters
get_hash = itemgetter('hash')
get_from = itemgetter('from')
get_to = itemgetter('to')
get_value = itemgetter('value')
get_gas = itemgetter('gas')
get_gas_price = itemgetter('gasPrice')
get_chain_id = itemgetter('chainId')
get_hash = itemgetter('hash')
get_parent_hash = itemgetter('parentHash')
get_block_number = itemgetter('number')
get_block_time = itemgetter('timestamp')

class EthereumProcessor(BaseProcessor):
    """
    Ethereum processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(sql_database, mongodb_database, 'Ethereum')
        self.querier = querier

    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        
        height = decode_hex(get_block_number(block))
        timestamp = decode_hex(get_block_time(block))
        
        self.logger.info(f"Processing block {height} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, height, timestamp)
        
        block_data = {
            "network": self.network,
            "block_number": height,
            "block_hash": decode_hex(get_hash(block)),
            "parent_hash": decode_hex(get_parent_hash(block)),
            "timestamp": timestamp,
        }
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {height} stored successfully.")
        
        # Process transactions
        self._process_transactions(block, height, timestamp)
        
        # Process withdrawals
        #self._process_withdrawals(block)
 
 
    
    def _process_transactions(self, block, block_number, timestamp):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        try:
            
            self.logger.info(f"Processing {self.network} transactions for block {block_number}")
            for transaction in block['transactions']:
                
                # Checks if the transaction is between two wallets, and then check the logs for data about the transaction
                #if normalize_hex(transaction['input']) == '0x':
                #   self._process_native_transfer(transaction, timestamp)
                
                # Format transaction data
                transaction_data = {
                    "block_number": block_number,
                    "transaction_hash": normalize_hex(get_hash(transaction)),
                    "chain_id" : self.get_chain_id_with_default(transaction),
                    "from_address": get_from(transaction),
                    "to_address": get_to(transaction),
                    "amount": decode_hex(get_value(transaction)),
                    "gas_costs": decode_hex(get_gas(transaction)) * decode_hex(get_gas_price(transaction)),
                    "timestamp": timestamp
                }
                # Store transaction data
                self.sql_insert_ops.insert_evm_transaction(self.network, transaction_data)
                self.logger.debug(f"Transaction {normalize_hex(transaction['hash'])} processed.")
            self.logger.info(f"Processed {len(block['transactions'])} {self.network} transactions for block {decode_hex(block['number'])}")
        
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {decode_hex(block['number'])}: {e}")
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 1
    
    def _process_native_transfer(self, transaction, timestamp):
        """
        Process native transfer transaction data.
        """
        transaction_data = {
                "block_number": transaction["blockNumber"],
                "transaction_hash": normalize_hex(transaction["hash"]),
                "from_address": transaction["from"],
                "to_address": transaction.get("to"),
                "amount": decode_hex(transaction.get("value")),
                "gas": decode_hex(transaction.get("gas")),
                "gas_price": decode_hex(transaction.get("gasPrice")),
                "timestamp": timestamp,
            }
        
        self.sql_insert_ops.insert_evm_transaction(self.network, transaction_data)
        self.logger.debug(f"Transaction {normalize_hex(transaction['hash'])} processed.")
    
 
 
 
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

