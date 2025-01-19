from dataclasses import dataclass
from typing import List

@dataclass
class EventSignature:
    signature_hash: str
    name: str
    full_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]
    inputs: List[dict]
    contract_address: str
