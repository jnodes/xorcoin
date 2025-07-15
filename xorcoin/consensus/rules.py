"""
Consensus rules for Xorcoin
"""
import time
from typing import List, Optional
from xorcoin.core.models import Block, Transaction

class ConsensusRules:
    # Network parameters
    MAX_BLOCK_SIZE = 1_000_000  # 1MB
    MAX_BLOCK_SIGOPS = 20_000
    COINBASE_MATURITY = 100
    DIFFICULTY_ADJUSTMENT_INTERVAL = 2016
    TARGET_BLOCK_TIME = 600  # 10 minutes
    MAX_TIME_DRIFT = 2 * 60 * 60  # 2 hours
    
    @staticmethod
    def validate_block_size(block: Block) -> bool:
        """Validate block doesn't exceed size limits"""
        # Serialize and check size
        block_size = len(str(block).encode())
        return block_size <= ConsensusRules.MAX_BLOCK_SIZE
    
    @staticmethod
    def validate_timestamp(block: Block, previous_block: Block) -> bool:
        """Validate block timestamp"""
        current_time = int(time.time())
        
        # Check not too far in future
        if block.timestamp > current_time + ConsensusRules.MAX_TIME_DRIFT:
            return False
            
        # Check not before previous block
        if block.timestamp <= previous_block.timestamp:
            return False
            
        return True
    
    @staticmethod
    def calculate_next_difficulty(chain: List[Block]) -> int:
        """Calculate difficulty adjustment"""
        if len(chain) < ConsensusRules.DIFFICULTY_ADJUSTMENT_INTERVAL:
            return chain[-1].difficulty
            
        # Get blocks for adjustment period
        period_start = chain[-ConsensusRules.DIFFICULTY_ADJUSTMENT_INTERVAL]
        period_end = chain[-1]
        
        time_taken = period_end.timestamp - period_start.timestamp
        expected_time = ConsensusRules.DIFFICULTY_ADJUSTMENT_INTERVAL * ConsensusRules.TARGET_BLOCK_TIME
        
        # Adjust difficulty
        new_difficulty = period_end.difficulty
        if time_taken < expected_time / 2:
            new_difficulty += 1  # Make harder
        elif time_taken > expected_time * 2:
            new_difficulty = max(1, new_difficulty - 1)  # Make easier
            
        return new_difficulty
