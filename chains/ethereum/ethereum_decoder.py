from web3 import Web3
import abi_codec
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

get_topics = itemgetter("topics")

class EthereumDecoder:
    def __init__(self):
        self.known_events = {}
        self.logger = logger
    
    
    # We already check if there is an event signature, so we can decode the log
    def decode_event(self, log, abi):
        try:
            # Get the event signature from log
            event_signature = get_topics(log)[0].hex()
            
            if event_signature not in self.known_events:
                # Add to known events
                self.map_signatures_to_known_events(abi)

            # Get the event ABI, actual event (not encoded)
            get_event_abi = itemgetter(event_signature)
            
            # Get the event ABI, actual event (not encoded)
            event = get_event_abi(self.known_events)
            
            return event
        except Exception as e:
            self.logger.error(f"Error decoding log: {e}")
            return None

    # Takes in an ABI
    def add_to_known_events(self, abi):
        try:
            # Get all the events from the ABI
            events = [item for item in abi if item["type"] == "event"]
            # Using the ABI determine the event
            for event in events:
                text = event["name"] + "(" + ",".join([input["type"] for input in event["inputs"]]) + ")"
                # Hash the event into a signature
                hashed_signature = Web3.keccak(text=text).hex()
                # Maps the signature to the event
                self.known_events[hashed_signature] = text
        except Exception as e:
            self.logger.error(f"Error mapping signatures to events: {e}")
            return None
    
    def decode_parameters(self, log, abi, event):
        try:
            
            return decoded_log
        except Exception as e:
            self.logger.error(f"Error decoding parameters: {e}")
            return None