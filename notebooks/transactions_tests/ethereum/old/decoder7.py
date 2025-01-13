from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
from datetime import datetime, timedelta
import numpy as np
import json
from web3 import Web3
from eth_abi.codec import ABICodec
from eth_abi.registry import registry
from concurrent.futures import ThreadPoolExecutor
import requests
from contextlib import contextmanager
import sqlite3


abi_codec = ABICodec(registry)
web3 = Web3()

@dataclass
class UndecodedLog:
    tx_hash: str
    log_index: int
    contract: str
    signature: str
    raw_log: dict

class EventSignature:
    signature_hash: str
    name: str
    full_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_database()
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
            
    def setup_database(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS known_events (
                    signature_hash TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_signature TEXT NOT NULL,
                    input_types TEXT NOT NULL,
                    indexed_inputs TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS contract_abis (
                    address TEXT PRIMARY KEY,
                    abi TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS undecoded_logs (
                    tx_hash TEXT,
                    log_index INTEGER,
                    contract TEXT,
                    signature TEXT,
                    raw_log TEXT,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 1,
                    PRIMARY KEY (tx_hash, log_index)
                );
                
                CREATE INDEX IF NOT EXISTS idx_signature_hash ON known_events(signature_hash);
                CREATE INDEX IF NOT EXISTS idx_contract_address ON contract_abis(address);
                CREATE INDEX IF NOT EXISTS idx_undecoded_signature ON undecoded_logs(signature);
            """)

    def store_undecoded_log(self, log: UndecodedLog):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO undecoded_logs 
                (tx_hash, log_index, contract, signature, raw_log)
                VALUES (?, ?, ?, ?, ?)
            """, (
                log.tx_hash,
                log.log_index,
                log.contract,
                log.signature,
                json.dumps(log.raw_log)
            ))

    def get_undecoded_logs(self, batch_size: int = 1000) -> List[UndecodedLog]:
        with self.get_connection() as conn:
            results = conn.execute("""
                SELECT tx_hash, log_index, contract, signature, raw_log 
                FROM undecoded_logs 
                ORDER BY last_attempt ASC 
                LIMIT ?
            """, (batch_size,)).fetchall()
            
            return [
                UndecodedLog(
                    tx_hash=row[0],
                    log_index=row[1],
                    contract=row[2],
                    signature=row[3],
                    raw_log=json.loads(row[4])
                )
                for row in results
            ]

    def remove_decoded_log(self, tx_hash: str, log_index: int):
        with self.get_connection() as conn:
            conn.execute("""
                DELETE FROM undecoded_logs 
                WHERE tx_hash = ? AND log_index = ?
            """, (tx_hash, log_index))

    def update_attempt_count(self, tx_hash: str, log_index: int):
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE undecoded_logs 
                SET attempts = attempts + 1,
                    last_attempt = CURRENT_TIMESTAMP
                WHERE tx_hash = ? AND log_index = ?
            """, (tx_hash, log_index))
@dataclass
class LogPattern:
    topic_count: int
    data_length: int
    indexed_count: int
    signature: str
    
    def __hash__(self):
        return hash((self.topic_count, self.data_length, self.indexed_count, self.signature))

class SmartReprocessingManager:
    def __init__(self, db_manager, max_pattern_distance: float = 0.2):
        self.db = db_manager
        self.contract_graph = nx.Graph()
        self.contract_success_rates = {}
        self.signature_frequencies = Counter()
        self.pattern_groups = defaultdict(list)
        self.max_pattern_distance = max_pattern_distance
        
    def extract_log_pattern(self, log: dict) -> LogPattern:
        """Extract pattern features from a log"""
        topics = log.get('topics', [])
        return LogPattern(
            topic_count=len(topics),
            data_length=len(log.get('data', '0x')) - 2,
            indexed_count=sum(1 for t in topics if len(t) == 66),
            signature=topics[0].hex() if topics else ''
        )
    
    def calculate_pattern_similarity(self, pattern1: LogPattern, pattern2: LogPattern) -> float:
        """Calculate similarity between two log patterns"""
        if pattern1.signature == pattern2.signature:
            return 1.0
            
        # Normalize features
        topic_diff = abs(pattern1.topic_count - pattern2.topic_count) / max(pattern1.topic_count, 1)
        data_diff = abs(pattern1.data_length - pattern2.data_length) / max(pattern1.data_length, 1)
        indexed_diff = abs(pattern1.indexed_count - pattern2.indexed_count) / max(pattern1.indexed_count, 1)
        
        # Weight the differences
        return 1.0 - (0.4 * topic_diff + 0.4 * data_diff + 0.2 * indexed_diff)

    def update_contract_graph(self):
        """Build and update contract interaction graph"""
        with self.db.get_connection() as conn:
            # Get recent contract interactions
            interactions = conn.execute("""
                SELECT DISTINCT l1.contract as from_contract, 
                               l2.contract as to_contract,
                               COUNT(*) as interaction_count
                FROM undecoded_logs l1
                JOIN undecoded_logs l2 
                    ON l1.tx_hash = l2.tx_hash 
                    AND l1.contract != l2.contract
                GROUP BY l1.contract, l2.contract
            """).fetchall()
            
            # Update graph
            self.contract_graph.clear()
            for from_contract, to_contract, weight in interactions:
                self.contract_graph.add_edge(
                    from_contract, 
                    to_contract, 
                    weight=weight
                )

    def update_contract_stats(self):
        """Update contract success rates and signature frequencies"""
        with self.db.get_connection() as conn:
            # Get contract success rates
            contract_stats = conn.execute("""
                SELECT contract,
                       COUNT(*) as total_attempts,
                       SUM(CASE WHEN attempts > 1 THEN 1 ELSE 0 END) as failed_attempts
                FROM undecoded_logs
                GROUP BY contract
            """).fetchall()
            
            self.contract_success_rates = {
                contract: 1 - (failed / total)
                for contract, total, failed in contract_stats
            }
            
            # Get signature frequencies
            signatures = conn.execute("""
                SELECT signature, COUNT(*) as freq
                FROM undecoded_logs
                GROUP BY signature
            """).fetchall()
            
            self.signature_frequencies.clear()
            self.signature_frequencies.update({sig: freq for sig, freq in signatures})

    def get_related_contracts(self, contract: str, depth: int = 2) -> Set[str]:
        """Get related contracts from the interaction graph"""
        if contract not in self.contract_graph:
            return {contract}
            
        related = set()
        current = {contract}
        
        for _ in range(depth):
            neighbors = set()
            for c in current:
                neighbors.update(self.contract_graph.neighbors(c))
            current = neighbors - related
            related.update(current)
            
        return related

    def group_logs_by_pattern(self, logs: List[dict]) -> Dict[LogPattern, List[dict]]:
        """Group logs by similar patterns"""
        pattern_groups = defaultdict(list)
        
        for log in logs:
            pattern = self.extract_log_pattern(log)
            
            # Find best matching pattern group or create new one
            best_match = None
            best_similarity = 0
            
            for existing_pattern in pattern_groups.keys():
                similarity = self.calculate_pattern_similarity(pattern, existing_pattern)
                if similarity > best_similarity and similarity >= self.max_pattern_distance:
                    best_similarity = similarity
                    best_match = existing_pattern
            
            if best_match:
                pattern_groups[best_match].append(log)
            else:
                pattern_groups[pattern].append(log)
                
        return pattern_groups

    def prioritize_logs(self, limit: int = 1000) -> List[dict]:
        """Get prioritized logs for reprocessing"""
        self.update_contract_graph()
        self.update_contract_stats()
        
        with self.db.get_connection() as conn:
            # Get all undecoded logs
            logs = conn.execute("""
                SELECT * FROM undecoded_logs
                WHERE attempts < 5
                ORDER BY last_attempt ASC
                LIMIT ?
            """, (limit * 2,)).fetchall()  # Get more than needed for better grouping
            
            if not logs:
                return []
                
            # Convert to list of dicts
            logs = [dict(log) for log in logs]
            
            # Score each log
            scored_logs = []
            for log in logs:
                contract = log['contract']
                signature = log['signature']
                
                # Calculate score components
                contract_score = self.contract_success_rates.get(contract, 0.5)
                signature_score = min(self.signature_frequencies[signature] / 100, 1.0)
                
                # Get related contract score
                related_contracts = self.get_related_contracts(contract)
                related_score = sum(
                    self.contract_success_rates.get(c, 0.5) 
                    for c in related_contracts
                ) / max(len(related_contracts), 1)
                
                # Combined score
                score = (
                    0.4 * contract_score +
                    0.3 * signature_score +
                    0.3 * related_score
                )
                
                scored_logs.append((score, log))
            
            # Sort by score and take top logs
            scored_logs.sort(reverse=True)
            prioritized_logs = [log for _, log in scored_logs[:limit]]
            
            # Group by pattern
            pattern_groups = self.group_logs_by_pattern(prioritized_logs)
            
            # Reorder logs to keep similar patterns together
            final_logs = []
            for pattern_group in pattern_groups.values():
                final_logs.extend(pattern_group)
            
            return final_logs[:limit]

class LogDecoder3:
    def smart_reprocess_logs(
        self,
        batch_size: int = 1000,
        min_success_rate: float = 0.1,
        max_attempts: int = 3
    ) -> int:
        """
        Smart reprocessing of logs using combined strategies
        """
        reprocessing_manager = SmartReprocessingManager(self.db)
        total_decoded = 0
        attempt = 0
        
        while attempt < max_attempts:
            # Get prioritized logs
            logs_to_process = reprocessing_manager.prioritize_logs(batch_size)
            if not logs_to_process:
                break
                
            # Process the logs
            decoded_results = self.process_transaction_logs(
                logs_to_process,
                store_undecoded=False  # Don't store as undecoded again
            )
            
            # Count successful decodings
            successful = 0
            for tx_hash, events in decoded_results.items():
                for event in events:
                    if (
                        event.get("event") != "Unknown" 
                        and "decode_error" not in event
                        and "raw_log" not in event
                    ):
                        successful += 1
                        # Remove from undecoded logs
                        log = next(l for l in logs_to_process if l['tx_hash'] == tx_hash)
                        self.db.remove_decoded_log(log['tx_hash'], log['log_index'])
            
            success_rate = successful / len(logs_to_process)
            total_decoded += successful
            attempt += 1
            
            print(f"Attempt {attempt}: Decoded {successful}/{len(logs_to_process)} logs "
                  f"(Success rate: {success_rate:.2%})")
            
            if success_rate < min_success_rate:
                break
                
        return total_decoded
    
    def __init__(self, etherscan_api_key: str, db_path: str):
        self.etherscan_api_key = etherscan_api_key
        self.db = DatabaseManager(db_path)
        self._session = requests.Session()
        self.unknown_logs = []
        
        # In-memory cache for hot paths
        self._event_cache: Dict[str, EventSignature] = {}
        self._abi_cache: Dict[str, dict] = {}
        
    def fetch_abi_from_explorer(self, contract_address: str) -> Optional[dict]:
        # Check memory cache first
        if contract_address in self._abi_cache:
            return self._abi_cache[contract_address]

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
                    self._abi_cache[contract_address] = abi
                    return abi
        except Exception as e:
            print(f"ABI fetch error for {contract_address}: {e}")
        return None

    def get_event_signature(self, event_abi: dict) -> EventSignature:
        name = event_abi["name"]
        inputs = event_abi["inputs"]
        input_types = [i["type"] for i in inputs]
        full_sig = f"{name}({','.join(input_types)})"
        sig_hash = Web3.keccak(text=full_sig).hex()
        indexed_inputs = [i.get("indexed", False) for i in inputs]
        
        return EventSignature(
            signature_hash=sig_hash,
            name=name,
            full_signature=full_sig,
            input_types=input_types,
            indexed_inputs=indexed_inputs
        )

    def decode_log(self, log: dict, event_sig: EventSignature) -> dict:
        try:
            topics = log.get("topics", [])
            if len(topics) < 1:
                return {"event": "Unknown", "raw_log": log}

            # Fast path for no parameters
            if not event_sig.input_types:
                return {"event": event_sig.name}

            topics = topics[1:]  # Skip first topic (event signature)
            data = log.get("data", "0x")
            
            result = {"event": event_sig.name}
            
            # Process indexed parameters
            for i, (topic, input_type, is_indexed) in enumerate(zip(
                topics, 
                event_sig.input_types, 
                event_sig.indexed_inputs
            )):
                if not is_indexed:
                    continue
                    
                param_name = f"param{i+1}"
                if input_type in ["bytes", "string"]:
                    result[param_name] = topic.hex()
                else:
                    try:
                        value = abi_codec.decode(
                            [input_type], 
                            bytes.fromhex(topic.hex())
                        )[0]
                        result[param_name] = value
                    except Exception as e:
                        result[param_name] = f"DecodeError: {str(e)}"

            # Process non-indexed parameters
            if data != "0x":
                non_indexed_types = [
                    t for t, idx in zip(event_sig.input_types, event_sig.indexed_inputs)
                    if not idx
                ]
                try:
                    values = abi_codec.decode(
                        non_indexed_types,
                        bytes.fromhex(data.hex())
                    )
                    for j, value in enumerate(values):
                        result[f"param{len(topics)+j+1}"] = value
                except Exception as e:
                    result["data_decode_error"] = str(e)

            return result

        except Exception as e:
            return {
                "event": event_sig.name,
                "decode_error": str(e),
                "raw_log": log
            }

    def decode_log_without_abi(self, log: dict) -> dict:
        """Fallback decoder for logs without ABI"""
        try:
            topics = log.get("topics", [])
            if not topics:
                return {"event": "Unknown", "raw_log": log}

            event_signature = topics[0].hex()
            
            # Basic decoding of topics and data
            result = {
                "event": "Unknown",
                "signature": event_signature,
                "topics": [t.hex() for t in topics[1:]],  # Convert remaining topics to hex
            }
            
            # Try to decode data if present
            data = log.get("data")
            if data and data != "0x":
                try:
                    # Split data into 32-byte chunks
                    data = data[2:]  # Remove '0x'
                    chunks = [data[i:i+64] for i in range(0, len(data), 64)]
                    result["data_chunks"] = chunks
                except Exception as e:
                    result["data_decode_error"] = str(e)
                    
            return result
            
        except Exception as e:
            return {
                "event": "Unknown",
                "decode_error": str(e),
                "raw_log": log
            }

    def decode_batch(self, logs_chunk: List[dict]) -> Dict[str, List[dict]]:
        decoded = defaultdict(list)
        
        # Process each log individually to ensure no logs are missed
        for log in logs_chunk:
            log = dict(log)
            try:
                # Get transaction hash - handle both string and HexBytes
                tx_hash = log["transactionHash"]
                if hasattr(tx_hash, 'hex'):
                    tx_hash = tx_hash.hex()
                if not tx_hash.startswith('0x'):
                    tx_hash = '0x' + tx_hash
                    
                contract_addr = log.get("address")
                topics = log.get("topics", [])
                
                if not contract_addr or not topics:
                    decoded_log = {
                        "event": "Unknown",
                        "error": "Missing contract address or topics",
                        "raw_log": log
                    }
                else:
                    # Try to decode with ABI first
                    decoded_log = None
                    abi = self._abi_cache.get(contract_addr) or self.fetch_abi_from_explorer(contract_addr)
                    
                    if abi:
                        event_signature = topics[0].hex()
                        event_sig = self._event_cache.get(event_signature)
                        
                        if not event_sig:
                            # Search for matching event in ABI
                            for event in (e for e in abi if e["type"] == "event"):
                                new_sig = self.get_event_signature(event)
                                if new_sig.signature_hash == event_signature:
                                    event_sig = new_sig
                                    self._event_cache[event_signature] = event_sig
                                    self.db.cache_event(event_sig)
                                    break
                                    
                        if event_sig:
                            decoded_log = self.decode_log(log, event_sig)
                    
                    # Fallback to basic decoding if ABI decoding failed
                    if not decoded_log:
                        decoded_log = self.decode_log_without_abi(log)
                
                # Always include contract address in decoded log
                decoded_log["contract"] = contract_addr
                decoded[tx_hash].append(decoded_log)
                
            except Exception as e:
                # Catch-all to ensure no transaction is missed
                error_log = {
                    "event": "DecodingError",
                    "error": str(e),
                    "raw_log": log
                }
                try:
                    tx_hash = log["transactionHash"].hex()
                    error_log["contract"] = log.get("address")
                    decoded[tx_hash].append(error_log)
                except:
                    # If we can't even get the transaction hash, add to unknown logs
                    self.unknown_logs.append(error_log)
        
        return dict(decoded)
    
    def store_undecoded_log(self, log: dict, reason: str = "Unknown"):
        """Store an undecoded log for later processing"""
        try:
            tx_hash = log["transactionHash"]
            if hasattr(tx_hash, 'hex'):
                tx_hash = tx_hash.hex()
            
            undecoded = UndecodedLog(
                tx_hash=tx_hash,
                log_index=log.get("logIndex", 0),
                contract=log.get("address", ""),
                signature=log["topics"][0].hex() if log.get("topics") else "",
                raw_log=log
            )
            self.db.store_undecoded_log(undecoded)
            
        except Exception as e:
            print(f"Error storing undecoded log: {e}")

    def reprocess_undecoded_logs(self, batch_size: int = 1000) -> Tuple[int, int]:
        """
        Reprocess previously undecoded logs using updated event signatures
        Returns: (successfully_decoded, total_processed)
        """
        undecoded_logs = self.db.get_undecoded_logs(batch_size)
        if not undecoded_logs:
            return 0, 0

        successfully_decoded = 0
        total_processed = len(undecoded_logs)
        
        # Process in smaller batches
        decoded_results = self.process_transaction_logs(
            [log.raw_log for log in undecoded_logs],
            batch_size=100
        )
        
        # Check which logs were successfully decoded
        for log in undecoded_logs:
            decoded_events = decoded_results.get(log.tx_hash, [])
            
            found_successful_decode = False
            for decoded_event in decoded_events:
                if (
                    decoded_event.get("event") != "Unknown" 
                    and "decode_error" not in decoded_event
                    and "raw_log" not in decoded_event
                ):
                    successfully_decoded += 1
                    found_successful_decode = True
                    self.db.remove_decoded_log(log.tx_hash, log.log_index)
                    break
            
            if not found_successful_decode:
                self.db.update_attempt_count(log.tx_hash, log.log_index)

        return successfully_decoded, total_processed

    def process_transaction_logs(
        self, 
        logs: List[dict], 
        batch_size: int = 100,
        max_workers: int = 4,
        store_undecoded: bool = True
    ) -> Dict[str, List[dict]]:
        """
        Process transaction logs with option to store undecoded logs
        """
        # Split logs into batches
        batches = [
            logs[i:i + batch_size] 
            for i in range(0, len(logs), batch_size)
        ]
        
        # Process batches in parallel
        decoded_transactions = defaultdict(list)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.decode_batch, batches))
            
        # Merge results and track undecoded logs
        for result in results:
            for tx_hash, decoded_logs in result.items():
                for log in decoded_logs:
                    decoded_transactions[tx_hash].append(log)
                    
                    # Store undecoded logs if requested
                    if store_undecoded and (
                        log.get("event") == "Unknown" 
                        or "decode_error" in log 
                        or "raw_log" in log
                    ):
                        self.store_undecoded_log(
                            log.get("raw_log", log),
                            reason="Failed to decode"
                        )
                
        return dict(decoded_transactions)

    def continuous_reprocessing(
        self,
        batch_size: int = 1000,
        min_success_rate: float = 0.1,
        max_attempts: int = 3
    ):
        """
        Continuously reprocess undecoded logs until success rate drops below threshold
        or max attempts reached
        """
        total_decoded = 0
        attempt = 0
        
        while attempt < max_attempts:
            decoded, total = self.reprocess_undecoded_logs(batch_size)
            if total == 0:
                break
                
            success_rate = decoded / total
            total_decoded += decoded
            attempt += 1
            
            print(f"Attempt {attempt}: Decoded {decoded}/{total} logs "
                  f"(Success rate: {success_rate:.2%})")
            
            if success_rate < min_success_rate:
                break
                
        return total_decoded