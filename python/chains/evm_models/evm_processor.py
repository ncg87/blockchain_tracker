from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from abc import abstractmethod
from operator import itemgetter
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
import asyncio

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

    def schedule_shutdown(self, delay_hours=24):
        """Schedule an automatic shutdown after specified hours"""
        def shutdown_timer():
            time.sleep(delay_hours * 3600)  # Convert hours to seconds
            self.logger.info(f"Automatic shutdown triggered after {delay_hours} hours")
            self.shutdown()

        shutdown_thread = threading.Thread(target=shutdown_timer, daemon=True)
        shutdown_thread.start()

    def _start_processing_workers(self):
        """Start background workers for continuous processing"""
        def process_worker():
            while not self._shutdown_flag.is_set():
                try:
                    batch = self.log_queue.get(timeout=1)  # 1 second timeout
                    if batch is None:
                        break
                    result = self._process_logs_batch_python(batch, self.abi_cache)
                    self.result_queue.put(result)
                except Empty:
                    continue  # Keep checking shutdown flag
                except Exception as e:
                    self.logger.error(f"Worker error: {e}")
                    
        self.workers = []
        for _ in range(8):  # Number of worker threads
            worker = threading.Thread(
                target=process_worker, 
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
            self.mongodb_insert_ops.insert_block(block, self.network, block_number, timestamp)
            self.logger.info(f"Inserted block {block_number} into {self.network} collection in MongoDB.")
            
            # Insert block into PostgreSQL
            self.sql_insert_ops.insert_block(
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
                asyncio.get_event_loop().run_in_executor(
                    None,
                    self.process_logs,
                    block_number,
                    timestamp
                )
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
                self.sql_insert_ops.insert_bulk_evm_transactions(
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
    
    def process_logs(self, block_number, timestamp, batch_size=1000, max_workers=8):
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
            
            # Submit batches to worker queue
            for batch in batches:
                self.log_queue.put(batch)
            
            # Collect results
            decoder_logs = defaultdict(list)
            for _ in range(len(batches)):
                batch_result = self.result_queue.get()
                for tx_hash, decoded_logs in batch_result.items():
                    decoder_logs[tx_hash].extend(decoded_logs)
            
            # Bulk insert into MongoDB
            if decoder_logs:
                self.mongodb_insert_ops.insert_evm_transactions(
                    dict(decoder_logs), 
                    self.network, 
                    block_number, 
                    timestamp
                )
            
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

    def _process_logs_batch_python(self, log_chunk, pre_loaded_abis):
        # This is a good candidate for Rust optimization
        decoded_logs = defaultdict(list)
        
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
                    
        return decoded_logs

    def get_contract_abi(self, address):
        # First try to get ABI from DB
        
        result = self.sql_query_ops.query_evm_contract_abi(self.network, address)
        if result:
            return json.loads(result.get('abi'))
        # If not found, try to get it from Etherscan
        abi = self.querier.get_contract_abi(address)
        if abi:
            # If found, store it in DB
            self.sql_insert_ops.insert_evm_contract_abi(self.network, address, abi)
        return abi
    
    
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
