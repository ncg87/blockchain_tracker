from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from queue import Queue, Empty
import threading
from psycopg2.pool import ThreadedConnectionPool
from config import Settings
import signal
import time
import os
from .cache import BoundedCache
from dataclasses import dataclass
import asyncio
from web3 import Web3
from .processing import EventProcessingSystem, TokenSwap
# Common item getters
get_hash = itemgetter('hash')
get_from = itemgetter('from')
get_to = itemgetter('to')
get_value = itemgetter('value')
get_gas = itemgetter('gas')
get_gas_price = itemgetter('gasPrice')
get_chain_id = itemgetter('chainId')
get_parent_hash = itemgetter('parentHash')
get_block_number = itemgetter('number')
get_block_time = itemgetter('timestamp')
get_logs = itemgetter('logs')
get_address = itemgetter('address')
get_topics = itemgetter('topics')
get_transaction_hash = itemgetter('transactionHash')

class EVMProcessor(BaseProcessor):
    """
    Abstract EVM processor class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier, decoder):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.decoder = decoder
        self.event_processor = EventProcessingSystem(sql_database, mongodb_database, network_name)
        
        # Initialize connection pool
        self.db_pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            **Settings.POSTGRES_CONFIG
        )
        
        # Processing queues
        self.log_queue = Queue(maxsize=10000)
        self.result_queue = Queue(maxsize=10000)
        
        # Replace simple dict with BoundedCache for ABI caching
        self.abi_cache = BoundedCache(max_size=1000, ttl_hours=24)
        
        # Shutdown flag
        self._shutdown_flag = threading.Event()
        
        # Start background workers
        self._start_processing_workers()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        self.shutdown()

    def schedule_shutdown(self, delay_seconds=86400):  # Default 24 hours in seconds
        """Schedule an automatic shutdown after specified seconds"""
        def shutdown_timer():
            time.sleep(delay_seconds)
            self.logger.info(f"Automatic shutdown triggered after {delay_seconds} seconds")
            self.shutdown()

        shutdown_thread = threading.Thread(target=shutdown_timer, daemon=True)
        shutdown_thread.start()

    def _start_processing_workers(self):
        """Start background workers for continuous processing"""
        async def process_worker():
            while not self._shutdown_flag.is_set():
                try:
                    batch_data = self.log_queue.get(timeout=1)  # 1 second timeout
                    if batch_data is None:
                        break
                    batch, timestamp = batch_data  # Unpack the tuple
                    result = await self._process_logs_batch_python(batch, self.abi_cache, timestamp)
                    self.result_queue.put(result)
                except Empty:
                    continue  # Keep checking shutdown flag
                except Exception as e:
                    self.logger.error(f"Worker error: {e}")
                    
        self.workers = []
        for _ in range(8):  # Number of worker threads
            worker = threading.Thread(
                target=lambda: asyncio.run(process_worker()), 
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

    async def process_block(self, block):
        """
        Process a block, transactions and logs concurrently.
        """
        try:
            block_number = decode_hex(get_block_number(block))
            timestamp = decode_hex(get_block_time(block))
            
            self.logger.info(f"Processing block {block_number} on {self.network}")
            
            # Insert block into MongoDB
            self.db_operator.mongodb.insert.insert_block(block, self.network, block_number, timestamp)
            self.logger.info(f"Inserted block {block_number} into {self.network} collection in MongoDB.")
            
            # Insert block into PostgreSQL
            self.db_operator.sql.insert.block.insert_block(
                self.network,
                block_number,
                normalize_hex(get_hash(block)),
                normalize_hex(get_parent_hash(block)),
                timestamp
            )
            self.logger.info(f"{self.network} block {block_number} inserted successfully")
            
            # Process transactions and logs concurrently
            await asyncio.gather(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    self._process_transactions,
                    block,
                    block_number,
                    timestamp
                ),
                self.process_logs(block_number, timestamp)
            )
            
            # Process withdrawals if they exist (e.g., for Ethereum post-merge)
            #if 'withdrawals' in block:
            #    await asyncio.get_event_loop().run_in_executor(
            #        None,
            #        self.process_withdrawals,
            #        block
            #    )
            
        except Exception as e:
            self.logger.error(f"Error processing block {block_number}: {e}", exc_info=True)
            raise

    def _process_transactions(self, block, block_number, timestamp):
        """
        Process raw transaction data in parallel batches.
        """
        try:
            transactions = block.get('transactions', [])
            if not transactions:
                return

            self.logger.info(f"Processing {len(transactions)} {self.network} transactions for block {block_number}")
            
            # Pre-process transactions into batches
            batch_size = 1000  # Adjust based on your needs
            transaction_batches = [
                transactions[i:i + batch_size] 
                for i in range(0, len(transactions), batch_size)
            ]
            
            # Process batches in parallel
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for batch in transaction_batches:
                    futures.append(
                        executor.submit(
                            self._process_transaction_batch,
                            batch,
                            block_number,
                            timestamp
                        )
                    )
                
                # Collect all processed transactions
                all_transactions = []
                for future in futures:
                    try:
                        batch_result = future.result()
                        all_transactions.extend(batch_result)
                    except Exception as e:
                        self.logger.error(f"Error processing transaction batch: {e}")
            
            # Bulk insert all transactions
            if all_transactions:
                self.db_operator.sql.insert.evm.insert_transactions(
                    self.network, 
                    all_transactions, 
                    block_number
                )
                
            self.logger.debug(f"Processed {len(transactions)} {self.network} transactions for block {block_number}")
            
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {block_number}: {e}")

    def _process_transaction_batch(self, transaction_batch, block_number, timestamp):
        """
        Process a batch of transactions.
        """
        try:
            processed_transactions = []
            for transaction in transaction_batch:
                try:
                    processed_tx = (
                        block_number,
                        self.network,
                        normalize_hex(get_hash(transaction)),
                        self.get_chain_id_with_default(transaction),
                        get_from(transaction),
                        get_to(transaction),
                        decode_hex(get_value(transaction)),
                        decode_hex(get_gas(transaction)) * decode_hex(get_gas_price(transaction)),
                        timestamp
                    )
                    processed_transactions.append(processed_tx)
                except Exception as e:
                    self.logger.error(f"Error processing individual transaction: {e}")
                    continue
                    
            return processed_transactions
            
        except Exception as e:
            self.logger.error(f"Error in transaction batch processing: {e}")
            return []
    
    @ abstractmethod
    def get_chain_id_with_default(self, tx):
        pass
    
    async def process_logs(self, block_number, timestamp, batch_size=1000, max_workers=8):
        """Optimized log processing with parallel execution"""
        block_number = decode_hex(block_number)
        timestamp = decode_hex(timestamp)
        
        try:
            logs = self.querier.get_block_logs(block_number)
            if not logs:
                return
            
            # Pre-fetch all unique contract addresses
            addresses = {log['address'] for log in logs if log.get('address')}
            
            # Bulk load ABIs
            for addr in addresses:
                # Use get() method from BoundedCache
                if self.abi_cache.get(addr) is None:
                    abi = self.get_contract_abi(addr)
                    if abi:
                        self.abi_cache.set(addr, abi)
            
            # Pre-fetch all event signatures
            event_signatures = {
                topics[0].hex() 
                for log in logs 
                if (topics := log.get('topics')) and topics
            }
            
            # Bulk load event signatures
            for sig in event_signatures:
                if self.decoder._event_signature_cache.get(sig) is None:
                    event_obj = self.decoder.sql_query_ops.query_evm_event(self.network, sig)
                    if event_obj:
                        self.decoder._event_signature_cache.set(sig, event_obj)
            
            # Process in parallel with pre-loaded data
            batches = [logs[i:i + batch_size] for i in range(0, len(logs), batch_size)]
            
            # Submit batches to worker queue with timestamp
            for batch in batches:
                self.log_queue.put((batch, timestamp))  # Modified to include timestamp
            
            # Collect results
            decoder_logs = defaultdict(list)
            for _ in range(len(batches)):
                batch_result = self.result_queue.get()
                for tx_hash, decoded_logs in batch_result.items():
                    decoder_logs[tx_hash].extend(decoded_logs)
            
            # Bulk insert into MongoDB
            if decoder_logs:
                self.db_operator.mongodb.insert.insert_evm_transactions(
                    dict(decoder_logs), 
                    self.network, 
                    block_number, 
                    timestamp
                )
            
            # Process events
            # Create tasks for all transaction events processing
            tasks = [
                self._process_transaction_events(tx_hash, decoded_logs, timestamp)
                for tx_hash, decoded_logs in decoder_logs.items()
            ]
            
            # Run all tasks concurrently and wait for completion
            if tasks:
                await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"Error processing logs for block {block_number}: {e}", exc_info=True)


    # Adjust to use Rust implementation
    def _process_logs_batch_optimized(self, log_chunk, pre_loaded_abis):
        try:
            # Convert to format Rust expects
            logs_for_rust = [self._prepare_log(log) for log in log_chunk]
            abis_for_rust = {addr: self._prepare_abi(abi) for addr, abi in pre_loaded_abis.items()}
            
            # Call Rust implementation
            return self._process_logs_batch_python(log_chunk, pre_loaded_abis)
        except Exception as e:
            self.logger.error(f"Error in Rust log processing: {e}")
            # Fallback to Python implementation
            return self._process_logs_batch_python(log_chunk, pre_loaded_abis)

    async def _process_logs_batch_python(self, log_chunk, pre_loaded_abis, timestamp):
        # This is a good candidate for Rust optimization
        decoded_logs = defaultdict(list)
        
        # Process logs concurrently
        tasks = []
        for log in log_chunk:
            log = dict(log)
            try:
                tx_hash = normalize_hex(get_transaction_hash(log))
                address = get_address(log)
                
                if not address or not log.get('topics'):
                    continue
                
                # Use get() method from BoundedCache
                abi = pre_loaded_abis.get(address)
                if abi is not None:
                    decoded_log = self.decoder.decode_log(log, abi)
                    decoded_log['contract'] = address
                    decoded_logs[tx_hash].append(decoded_log)
                    
                    # Create task for event processing
                    #task = asyncio.create_task(
                    #    self._process_transaction_event(decoded_log, tx_hash, timestamp)
                    #)
                    #tasks.append(task)
                    
            except Exception as e:
                error_log = {
                    "event": "DecodingError",
                    "error": str(e),
                    "raw_log": log
                }
                try:
                    tx_hash = log["transactionHash"].hex()
                    error_log["contract"] = log.get("address")
                    decoded_logs[tx_hash].append(error_log)
                except:
                    continue
        
        # Wait for all event processing to complete
        if tasks:
            await asyncio.gather(*tasks)
                    
        return decoded_logs

    def get_contract_abi(self, address):
        address = Web3.to_checksum_address(address)
        
        # First try to get ABI from DB
        result = self.sql_query_ops.query_evm_contract_abi(self.network, address)
        if result:
            abi = json.loads(result.get('abi'))
            return abi
        
        # If not found, try to get it from Etherscan
        abi = self.querier.get_contract_abi(address)
        
        if abi:
            # Store it in DB first
            self.db_operator.sql.insert.evm.insert_contract_abi(self.network, address, abi)
            
            # Schedule the contract processing asynchronously, to try to get the factory and info
            asyncio.create_task(self._process_contract(address, abi))
            
        return abi
    
    async def process_contract(self, address: str, update=True):
        abi = self.get_contract_abi(address)
        return await self._process_contract(address, abi, update)
    
    # Maybe make a batch version of this, with threading
    async def _process_contract(self, address, abi, update=False):
        try:
            address = Web3.to_checksum_address(address)
            # Check if contract info is already in DB
            contract_info = self.sql_query_ops.query_evm_swap(self.network, address)
            if contract_info and not update:
                return contract_info
            
            if type(abi) == str:
                abi = json.loads(abi)
            contract = self.querier.get_contract(address, abi)
            
            if not contract:
                return None
            # Get the factory of the contract
            factory = contract.functions.factory().call(),
            
            self.db_operator.sql.insert.evm.insert_contract_to_factory(self.network, address, factory)
            
            swap_methods = ['token0', 'token1', 'factory']
            for method in swap_methods:
                if not hasattr(contract.functions, method):
                    return None
            
            token0_address = contract.functions.token0().call()
            token1_address = contract.functions.token1().call()

            # Check for token0 info in DB
            token0_info = self.sql_query_ops.query_evm_token_info(self.network, token0_address)
            if not token0_info:
                # If not found, get it from the contract address
                token0_contract = self.querier.get_contract(token0_address, ERC20_ABI)
                token0_info = TokenInfo(
                    address=token0_address,
                    name=token0_contract.functions.name().call(),
                    symbol=token0_contract.functions.symbol().call(),
                    decimals=token0_contract.functions.decimals().call()
                )
                self.db_operator.sql.insert.evm.insert_token_info(self.network, token0_info)
            # Same thing for token1
            token1_info = self.sql_query_ops.query_evm_token_info(self.network, token1_address)
            if not token1_info:
                token1_contract = self.querier.get_contract(token1_address, ERC20_ABI)
                token1_info = TokenInfo(
                    address=token1_address,
                    name=token1_contract.functions.name().call(),
                    symbol=token1_contract.functions.symbol().call(),
                    decimals=token1_contract.functions.decimals().call()
                )
                self.db_operator.sql.insert.evm.insert_token_info(self.network, token1_info)
            
            # Try to get fee from contract, not crucial so well continue if it fails
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
            self.db_operator.sql.insert.evm.insert_swap(self.network, contract_info)
            return contract_info
        except Exception as e:
            self.logger.error(f"Error processing contract {contract}: {e}")
            return None
    
    async def _process_token(self, contract_address, update=False):
        try:
            token_info = self.sql_query_ops.query_evm_token_info(self.network, contract_address)
            if token_info and not update:
                return token_info
            
            token_contract = self.querier.get_contract(contract_address, ERC20_ABI)
            
            contract_address = Web3.to_checksum_address(contract_address)
            
            token_info = TokenInfo(
                address=contract_address,
                name=token_contract.functions.name().call(),
                symbol=token_contract.functions.symbol().call(),
                decimals=token_contract.functions.decimals().call()
            )
            self.db_operator.sql.insert.evm.insert_token_info(self.network, token_info)
            return token_info
        except Exception as e:
            self.logger.debug(f"Error processing token {contract_address}: {e}")
            return None
    
    
    async def _process_transaction_event(self, decoded_event, tx_hash, index, timestamp):
        try:
            return self.event_processor.process_event(decoded_event, tx_hash, index, timestamp)
        except Exception as e:
            self.logger.error(f"Error processing transaction event: {e}", exc_info=True)
            return None
    
    async def _process_transaction_events(self, tx_hash, decoded_logs, timestamp):
        try:
            events = []
            for i, event in enumerate(decoded_logs):
                event_info = await self._process_transaction_event(event, tx_hash, i, timestamp)
                if event_info:
                    events.append(event_info)
            return events
        except Exception as e:
            self.logger.error(f"Error processing transaction events: {e} - {decoded_logs}", exc_info=True)
    
    async def _process_swaps(self, address):
        contract_abi = self.sql_query_ops.query_evm_contract_abi('Ethereum', address)
        return await self._process_contract(address, contract_abi['abi'])
    
    def process_syncs(self, address):
        pass
    
    def process_withdrawals(self, block):
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

    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            # Set shutdown flag
            self._shutdown_flag.set()
            
            # Signal workers to stop
            for _ in self.workers:
                self.log_queue.put(None)
            
            # Wait for workers to finish with timeout
            shutdown_start = time.time()
            for worker in self.workers:
                remaining_time = max(0, 60 - (time.time() - shutdown_start))
                worker.join(timeout=remaining_time)
                
            # Close database pool
            if hasattr(self, 'db_pool'):
                self.db_pool.closeall()
                
            self.logger.info("Processor shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            # Force exit if cleanup takes too long
            if time.time() - shutdown_start > 65:  # 5 second grace period
                self.logger.warning("Forcing exit after timeout")
                os._exit(0)


ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str
    decimals: int

@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    token0_address: str
    token1_address: str
    name: str
