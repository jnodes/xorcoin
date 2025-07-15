"""
Block mining and blockchain operations for Xorcoin
"""

import time
import secrets
from .models import Block


class BlockMiner:
    """Handles block mining operations"""
    
    @staticmethod
    def mine_block(block: Block, target_difficulty: int = None) -> bool:
        """
        Proof-of-Work mining with secure nonce
        
        Args:
            block: The block to mine
            target_difficulty: Override block's difficulty if provided
            
        Returns:
            True if block was successfully mined
        """
        if target_difficulty:
            block.difficulty = target_difficulty
            
        block.merkle_root = block.calculate_merkle_root()
        target = "0" * block.difficulty
        attempts = 0
        start_time = time.time()
        
        print(f"Mining block at height {block.height} with difficulty {block.difficulty}...")
        
        while True:
            # Use cryptographically secure random nonce
            block.nonce = secrets.randbits(32)
            hash_result = block.get_header_hash()
            
            if hash_result.startswith(target):
                elapsed = time.time() - start_time
                print(f"Block mined! Hash: {hash_result}")
                print(f"Nonce: {block.nonce}, Attempts: {attempts}, Time: {elapsed:.2f}s")
                return True
                
            attempts += 1
            
            # Progress update every 100k attempts
            if attempts % 100000 == 0:
                elapsed = time.time() - start_time
                rate = attempts / elapsed
                print(f"Mining... Attempts: {attempts:,}, Rate: {rate:,.0f} H/s")


class Blockchain:
    """Simple blockchain implementation"""
    
    def __init__(self):
        self.chain: list[Block] = []
        self.difficulty = 4
        
    def add_genesis_block(self):
        """Create and add the genesis block"""
        genesis = Block(
            height=0,
            prev_block_hash="0" * 64,
            difficulty=self.difficulty
        )
        BlockMiner.mine_block(genesis)
        self.chain.append(genesis)
        
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain after validation"""
        if not self.chain:
            raise ValueError("Cannot add block to empty chain")
            
        # Set block properties
        block.height = len(self.chain)
        block.prev_block_hash = self.chain[-1].get_header_hash()
        block.difficulty = self.difficulty
        
        # Mine the block
        if BlockMiner.mine_block(block):
            self.chain.append(block)
            return True
        return False
        
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        if not self.chain:
            raise ValueError("Blockchain is empty")
        return self.chain[-1]
        
    def validate_chain(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check if the block is properly mined
            if not current.get_header_hash().startswith("0" * current.difficulty):
                return False
                
            # Check if previous hash matches
            if current.prev_block_hash != previous.get_header_hash():
                return False
                
            # Check if height is correct
            if current.height != i:
                return False
                
        return True
