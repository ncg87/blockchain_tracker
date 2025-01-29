from collections import defaultdict
import asyncio
import logging
from operator import itemgetter
from web3 import Web3
from ....utils import normalize_hex
from .cache import BoundedCache
from .decoder import EVMDecoder
import json
from database import DatabaseOperator
from .models import ContractInfo, TokenInfo

from ...evm_data import ERC20_ABI

# Log item getters
get_address = itemgetter('address')
get_topics = itemgetter('topics')
get_transaction_hash = itemgetter('transactionHash')

class LogProcessor:
    def __init__(self, db_operator: DatabaseOperator, querier, chain: str):
        self.db_operator = db_operator
        self.querier = querier
        self.chain = chain
        self.logger = logging.getLogger(__name__)
        self.batch_size = 1000
        
        # Initialize decoder
        self.decoder = EVMDecoder(self.db_operator, self.chain)
        
        # Initialize cache
        self.abi_cache = BoundedCache(max_size=1000, ttl_hours=24)

    async def process(self, block_number: int, timestamp: int, logs: list):
        """Process logs for a given block"""
        try:
            if not logs:
                return {}
            
            # Pre-fetch all unique contract addresses
            addresses = {log['address'] for log in logs if log.get('address')}
            
            # Bulk load ABIs concurrently
            abi_tasks = []
            for addr in addresses:
                if self.abi_cache.get(addr) is None:
                    abi_tasks.append(self._fetch_and_cache_abi(addr))
            if abi_tasks:
                await asyncio.gather(*abi_tasks)
            
            # Process in parallel with pre-loaded data
            batches = [logs[i:i + self.batch_size] for i in range(0, len(logs), self.batch_size)]
            
            # Create tasks for each batch
            tasks = [self._process_logs_batch(batch, timestamp) for batch in batches]
            batch_results = await asyncio.gather(*tasks)
            
            # Combine results
            decoder_logs = defaultdict(list)
            for batch_result in batch_results:
                for tx_hash, decoded_logs in batch_result.items():
                    decoder_logs[tx_hash].extend(decoded_logs)
            
            # Bulk insert into MongoDB
            if decoder_logs:
                self.db_operator.mongodb.insert.insert_evm_transactions(
                    dict(decoder_logs),
                    self.chain,
                    block_number,
                    timestamp
                )
            
            return decoder_logs
            
        except Exception as e:
            self.logger.error(f"Error processing logs for block {block_number}: {e}")
            raise

    async def _fetch_and_cache_abi(self, address):
        """Fetch and cache ABI for a contract address"""
        abi = await self.get_contract_abi(address)
        if abi:
            self.abi_cache.set(address, abi)

    async def _process_logs_batch(self, log_chunk: list, timestamp: int):
        """Process a batch of logs concurrently"""
        decoded_logs = defaultdict(list)
        
        # Process logs concurrently within the batch
        tasks = [self._process_single_log(log) for log in log_chunk]
        results = await asyncio.gather(*tasks)
        
        # Combine results
        for log_result in results:
            if log_result:
                tx_hash, decoded_log = log_result
                decoded_logs[tx_hash].append(decoded_log)
                
        return decoded_logs

    async def _process_single_log(self, log):
        """Process a single log"""
        try:
            tx_hash = normalize_hex(get_transaction_hash(log))
            address = get_address(log)
            
            if not address or not log.get('topics'):
                return None
            
            abi = self.abi_cache.get(address)
            if abi is not None:
                decoded_log = self.decoder.decode_log(log, abi)
                if decoded_log:
                    decoded_log['contract'] = address
                    return tx_hash, decoded_log
                    
        except Exception as e:
            self.logger.error(f"Error processing log: {e}")
            error_log = {
                "event": "DecodingError",
                "error": str(e),
                "raw_log": log
            }
            try:
                tx_hash = log["transactionHash"].hex()
                error_log["contract"] = log.get("address")
                return tx_hash, error_log
            except:
                return None
        
        return None

    async def get_contract_abi(self, address):
        """Get contract ABI with async support"""
        address = Web3.to_checksum_address(address)
        
        # First try to get ABI from DB
        result = self.db_operator.sql.query.evm.query_contract_abi(self.chain, address)
        if result:
            abi = json.loads(result.get('abi'))
            return abi
        
        # If not found, try to get it from Etherscan
        abi = await self.querier.get_contract_abi(address)
        
        if abi:
            # Store it in DB first
            self.db_operator.sql.insert.evm.contract_abi(self.chain, address, abi)
            
            # Schedule the contract processing asynchronously
            asyncio.create_task(self._process_contract(address, abi))
            
        return abi

    async def process_contract(self, address: str, update=True):
        abi = await self.get_contract_abi(address)
        return await self._process_contract(address, abi, update)
    
    async def _process_contract(self, address, abi, update=False):
        try:
            address = Web3.to_checksum_address(address)
            # Check if contract info is already in DB
            contract_info = self.db_operator.sql.query.evm.swap_info_by_network(self.chain, address)
            if contract_info and not update:
                return contract_info
            
            if type(abi) == str:
                abi = json.loads(abi)
            contract = self.querier.get_contract(address, abi)
            
            if not contract:
                return None
            # Get the factory of the contract
            factory = contract.functions.factory().call(),
            
            self.db_operator.sql.insert.evm.contract_to_factory(self.chain, address, factory)
            
            swap_methods = ['token0', 'token1', 'factory']
            for method in swap_methods:
                if not hasattr(contract.functions, method):
                    return None
            
            # Get the token0 and token1 addresses
            token0_address = contract.functions.token0().call()
            token1_address = contract.functions.token1().call()
            
            # Get the token0 and token1 info
            token0_info = await self._process_token(token0_address, update=update)
            token1_info = await self._process_token(token1_address, update=update)
            
            if not token0_info or not token1_info:
                return None
            
            # Try to get fee from contract, not crucial so continue if it fails
            try:
                fee = contract.functions.fee().call()
            except Exception as e:
                fee = None
            
            # Create contract info after obtaining all necessary info
            contract_info = ContractInfo(
                address=address,
                factory=factory,
                fee=fee,
                token0_name=token0_info.name,
                token1_name=token1_info.name,
                token0_address=token0_info.address,
                token1_address=token1_info.address,
                name=None # Exchange/Factory contract name
            )

            # Insert contract info into DB
            self.db_operator.sql.insert.evm.swap_info(self.chain, contract_info)
            
            return contract_info
        except Exception as e:
            self.logger.error(f"Error processing contract {contract}: {e}")
            return None
    
    async def _process_token(self, contract_address, update=False):
        try:
            
            contract_address = Web3.to_checksum_address(contract_address)
            
            # Check the database for the token info
            token_info = self.db_operator.sql.query.evm.token_info_by_chain(self.chain, contract_address)
            if token_info and not update:
                return token_info
            
            # If not found, get it from the contract address
            token_contract = self.querier.get_contract(contract_address, ERC20_ABI)
            
            # Package it nicely into a TokenInfo object
            token_info = TokenInfo(
                address=contract_address,
                name=token_contract.functions.name().call(),
                symbol=token_contract.functions.symbol().call(),
                decimals=token_contract.functions.decimals().call()
            )
            # Insert or update the token info into the database
            self.db_operator.sql.insert.evm.token_info(self.chain, token_info)
            
            return token_info
        except Exception as e:
            self.logger.info(f"Error processing token {contract_address}: {e}")
            return None
    
    
    async def _process_transaction_event(self, decoded_event, tx_hash, index, timestamp):
        try:
            return self.event_processor.process_event(decoded_event, tx_hash, index, timestamp)
        except Exception as e:
            self.logger.error(f"Error processing transaction event: {e}", exc_info=True)
            return None

