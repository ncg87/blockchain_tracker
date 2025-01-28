from dataclasses import dataclass

@dataclass
class Block:
    block_number: int
    block_hash: str
    parent_hash: str
    timestamp: int
    network: str