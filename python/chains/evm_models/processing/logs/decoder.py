from web3 import Web3
from operator import itemgetter
import logging
from eth_abi.codec import ABICodec
from eth_abi.registry import registry
from database import DatabaseOperator
from datetime import datetime
import threading
import time
from .cache import BoundedCache
from .models import EventSignature

get_name = itemgetter("name")
get_topics = itemgetter("topics")
get_type = itemgetter("type")
get_inputs = itemgetter("inputs")
get_address = itemgetter("address")
get_log_index = itemgetter("logIndex")

class EVMDecoder:
    def __init__(self, db_operator: DatabaseOperator, chain: str):
        self.db_operator = db_operator
        self.logger = logging.getLogger(__name__)
        self.abi_codec = ABICodec(registry)
        self.network = chain
        self._event_signature_cache = BoundedCache(max_size=1000, ttl_hours=24)
        self._start_cleanup_thread()
    
    
    # We already check if there is an event signature, so we can decode the log
    def decode_log(self, log, abi):
        try:
            # Get the event signature from log
            event_signature = get_topics(log)[0].hex()
            
            # Try to get the event from cache first
            event_object = self._event_signature_cache.get(event_signature)
            
            # If not in cache, try to get from DB
            if event_object is None:
                event_object = self.db_operator.sql.query.evm.event_by_chain(self.network, event_signature)
                # If found in DB, add to cache
                if event_object:
                    self._event_signature_cache.set(event_signature, event_object)
                # If not in DB, search ABI and add to both DB and cache
                else:
                    # Search for matching event in ABI
                    for event in (e for e in abi if e["type"] == "event"):
                        new_sig = self.get_event_signature(event)
                        if new_sig.signature_hash == event_signature:
                            event_object = new_sig
                            self.db_operator.sql.insert.evm.event(self.network, event_object)
                            self._event_signature_cache.set(event_signature, event_object)
                            break
            
            log_index = get_log_index(log)
            
            if event_object:
                decoded_log = self._decode_log(log, event_object)
            else:
                decoded_log = self.decode_log_without_abi(log)
            decoded_log["log_index"] = log_index
            return decoded_log
        

        except Exception as e:
            self.logger.error(f"Error decoding log for {self.network}: {e}", exc_info=True)
            return None
    
    def _decode_log(self, log: dict, event_sig: EventSignature) -> dict:
        try:
            topics = log.get("topics", [])
            if len(topics) < 1:
                return {"event": "Unknown", "raw_log": log}

            # Fast path for no parameters
            if not event_sig.input_types:
                return {"event": event_sig.event_name}

            topics = topics[1:]  # Skip first topic (event signature)
            data = log.get("data", "0x")
            
            result = {"event": event_sig.event_name,
                      "parameters": {}
                      }
            
            input_names = event_sig.input_names
            input_descriptions = [i.get("description", "") for i in event_sig.inputs]
            
             # Process indexed parameters
            topic_index = 0
            for i, (input_type, is_indexed, input_name, description) in enumerate(zip(
                event_sig.input_types, 
                event_sig.indexed_inputs,
                input_names,
                input_descriptions
            )):
                if not is_indexed:
                    continue
                    
                if topic_index >= len(topics):
                    break
                    
                topic = topics[topic_index]
                topic_index += 1
                
                if input_type in ["bytes", "string"]:
                    value = topic.hex()
                else:
                    try:
                        value = self.abi_codec.decode(
                            [input_type], 
                            bytes.fromhex(topic.hex())
                        )[0]
                    except Exception as e:
                        value = f"DecodeError: {str(e)}"
                
                result["parameters"][input_name] = {
                    "value": value,
                    "type": input_type,
                    "indexed": True,
                    "description": description if description else None
                }

            # Process non-indexed parameters
            if data != "0x":
                non_indexed_info = [
                    (t, name, desc) 
                    for t, idx, name, desc in zip(event_sig.input_types, event_sig.indexed_inputs, input_names, input_descriptions)
                    if not idx
                ]
                try:
                    values = self.abi_codec.decode(
                        [t for t, _, _ in non_indexed_info],
                        bytes.fromhex(data.hex())
                    )
                    for (input_type, name, description), value in zip(non_indexed_info, values):
                        result["parameters"][name] = {
                            "value": value,
                            "type": input_type,
                            "indexed": False,
                            "description": description if description else None
                        }
                except Exception as e:
                    result["data_decode_error"] = str(e)

            return result

        except Exception as e:
            return {
                "event": event_sig.name,
                "decode_error": str(e),
                "raw_log": log
            }
    
    def get_event_signature(self, event_abi: dict) -> EventSignature:
        name = event_abi["name"]
        inputs = event_abi["inputs"]
        input_types = [i["type"] for i in inputs]
        input_names = [i["name"] for i in inputs]
        full_sig = f"{name}({','.join(input_types)})"
        sig_hash = Web3.keccak(text=full_sig).hex()
        indexed_inputs = [i.get("indexed", False) for i in inputs]
        
        return EventSignature(
            signature_hash=sig_hash,
            event_name=name,
            decoded_signature=full_sig,
            input_types=input_types,
            indexed_inputs=indexed_inputs,
            input_names=input_names,
            inputs=inputs,
        )
    
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

    def cleanup_cache(self):
        """Periodic cleanup of expired cache entries"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key for key, (_, timestamp) in self._event_signature_cache.cache.items()
                if current_time - timestamp > self._event_signature_cache.ttl
            ]
            for key in expired_keys:
                del self._event_signature_cache.cache[key]
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}", exc_info=True)

    def _start_cleanup_thread(self):
        """Start a background thread for cache cleanup"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self.cleanup_cache()
                except Exception as e:
                    self.logger.error(f"Cache cleanup thread error: {e}", exc_info=True)

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()



