from dataclasses import dataclass
from typing import List

@dataclass
class EventSignature:
    signature_hash: str
    event_name: str
    decoded_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]
    input_names: List[str]
    inputs: List[dict]
