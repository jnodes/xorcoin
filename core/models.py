"""
Core data structures for Xorcoin
"""

import hashlib
import time
import json
from typing import List
from dataclasses import dataclass, field


@dataclass
class UTXO:
    """Unspent Transaction Output"""
    tx_hash: str
    output_index: int
    amount: int
    script_pubkey: str  # Hash of public key (address)

    def get_id(self) -> str:
        """Get unique identifier for this UTXO"""
        return f"{self.tx_hash}:{self.output_index}"


@dataclass
class TxInput:
    """Transaction Input referencing a UTXO"""
    prev_tx_hash: str
    prev_output_index: int
    signature: bytes = b''
    pubkey: bytes = b''

    def get_utxo_id(self) -> str:
        """Get the UTXO ID this input references"""
        return f"{self.prev_tx_hash}:{self.prev_output_index}"


@dataclass
class TxOutput:
    """Transaction Output creating new UTXO"""
    amount: int
    script_pubkey: str


@dataclass
class Transaction:
    """Xorcoin transaction with security features"""
    version: int = 2
    chain_id: int = 1  # Replay protection
    inputs: List[TxInput] = field(default_factory=list)
    outputs: List[TxOutput] = field(default_factory=list)
    locktime: int = 0
    timestamp: int = field(default_factory=lambda: int(time.time()))

    def serialize_for_signing(self, input_index: int) -> bytes:
        """Serialize transaction for signing specific input"""
        data = {
            'version': self.version,
            'chain_id': self.chain_id,
            'timestamp': self.timestamp,
            'inputs': [
                {
                    'prev_tx_hash': inp.prev_tx_hash,
                    'prev_output_index': inp.prev_output_index
                } for inp in self.inputs
            ],
            'outputs': [
                {
                    'amount': out.amount,
                    'script_pubkey': out.script_pubkey
                } for out in self.outputs
            ],
            'locktime': self.locktime,
            'signing_input': input_index
        }
        return json.dumps(data, sort_keys=True).encode()

    def get_hash(self) -> str:
        """Calculate transaction hash (excluding signatures) to prevent malleability"""
        data = {
            'version': self.version,
            'chain_id': self.chain_id,
            'inputs': [
                {
                    'prev_tx_hash': inp.prev_tx_hash,
                    'prev_output_index': inp.prev_output_index
                } for inp in self.inputs
            ],
            'outputs': [
                {
                    'amount': out.amount,
                    'script_pubkey': out.script_pubkey
                } for out in self.outputs
            ],
            'locktime': self.locktime
        }
        tx_data = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(hashlib.sha256(tx_data).digest()).hexdigest()


@dataclass
class Block:
    """Xorcoin blockchain block"""
    version: int = 1
    height: int = 0
    timestamp: int = field(default_factory=lambda: int(time.time()))
    prev_block_hash: str = "0" * 64
    merkle_root: str = ""
    difficulty: int = 4
    nonce: int = 0
    transactions: List[Transaction] = field(default_factory=list)

    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            return "0" * 64
        
        tx_hashes = [tx.get_hash() for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            tx_hashes = new_hashes
        
        return tx_hashes[0]

    def get_header_hash(self) -> str:
        """Calculate block header hash"""
        header = {
            'version': self.version,
            'height': self.height,
            'timestamp': self.timestamp,
            'prev_block_hash': self.prev_block_hash,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'nonce': self.nonce
        }
        header_str = json.dumps(header, sort_keys=True)
        return hashlib.sha256(hashlib.sha256(header_str.encode()).digest()).hexdigest()
