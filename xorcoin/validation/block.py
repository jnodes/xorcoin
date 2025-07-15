"""
Enhanced block validation with security checks
"""
from typing import List, Set, Optional
from xorcoin.core.models import Block, Transaction
from xorcoin.consensus.rules import ConsensusRules

class BlockValidator:
    """Comprehensive block validation"""
    
    def __init__(self, utxo_set):
        self.utxo_set = utxo_set
        
    def validate_block(self, block: Block, previous_block: Block) -> bool:
        """Full block validation"""
        # 1. Check block structure
        if not self._validate_structure(block):
            return False
            
        # 2. Check proof of work
        if not self._validate_pow(block):
            return False
            
        # 3. Check timestamp
        if not ConsensusRules.validate_timestamp(block, previous_block):
            return False
            
        # 4. Check block size
        if not ConsensusRules.validate_block_size(block):
            return False
            
        # 5. Validate merkle root
        if not self._validate_merkle_root(block):
            return False
            
        # 6. Validate all transactions
        if not self._validate_transactions(block):
            return False
            
        # 7. Check coinbase transaction
        if not self._validate_coinbase(block):
            return False
            
        return True
        
    def _validate_structure(self, block: Block) -> bool:
        """Validate basic block structure"""
        if not block.transactions:
            print("Block has no transactions")
            return False
            
        if block.height < 0:
            print("Invalid block height")
            return False
            
        return True
        
    def _validate_pow(self, block: Block) -> bool:
        """Validate proof of work"""
        target = "0" * block.difficulty
        return block.get_header_hash().startswith(target)
        
    def _validate_merkle_root(self, block: Block) -> bool:
        """Validate merkle root matches transactions"""
        calculated = block.calculate_merkle_root()
        return calculated == block.merkle_root
        
    def _validate_transactions(self, block: Block) -> bool:
        """Validate all transactions in block"""
        used_utxos: Set[str] = set()
        
        # Skip coinbase (first transaction)
        for tx in block.transactions[1:]:
            # Check for double-spending within block
            for inp in tx.inputs:
                utxo_id = inp.get_utxo_id()
                if utxo_id in used_utxos:
                    print(f"Double-spend in block: {utxo_id}")
                    return False
                used_utxos.add(utxo_id)
                
        return True
        
    def _validate_coinbase(self, block: Block) -> bool:
        """Validate coinbase transaction"""
        if not block.transactions:
            return False
            
        coinbase = block.transactions[0]
        
        # Coinbase must have no inputs
        if coinbase.inputs:
            print("Coinbase has inputs")
            return False
            
        # Check coinbase amount (should include fees)
        # This is simplified - real implementation would calculate total fees
        if not coinbase.outputs:
            print("Coinbase has no outputs")
            return False
            
        return True
