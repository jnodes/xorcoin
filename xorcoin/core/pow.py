"""
Improved Proof-of-Work implementation
"""
import hashlib
import struct
from typing import Optional

class ProofOfWork:
    """Secure Proof-of-Work implementation"""
    
    @staticmethod
    def calculate_target(difficulty: int) -> int:
        """Calculate numeric target from difficulty"""
        if difficulty < 1:
            difficulty = 1
        # Target = 2^(256 - difficulty)
        return 2 ** (256 - difficulty)
        
    @staticmethod
    def hash_to_int(hash_hex: str) -> int:
        """Convert hash to integer for comparison"""
        return int(hash_hex, 16)
        
    @staticmethod
    def mine_block_secure(block, max_nonce: int = 2**32) -> Optional[int]:
        """
        Mine block with incremental nonce (more efficient than random)
        """
        target = ProofOfWork.calculate_target(block.difficulty)
        
        for nonce in range(max_nonce):
            block.nonce = nonce
            hash_result = block.get_header_hash()
            
            if ProofOfWork.hash_to_int(hash_result) < target:
                return nonce
                
        return None
        
    @staticmethod
    def verify_pow(block) -> bool:
        """Verify proof of work for a block"""
        target = ProofOfWork.calculate_target(block.difficulty)
        hash_int = ProofOfWork.hash_to_int(block.get_header_hash())
        return hash_int < target
        
    @staticmethod
    def calculate_next_work_required(blocks: list, target_timespan: int, target_spacing: int) -> int:
        """
        Calculate required difficulty for next block
        More sophisticated than current implementation
        """
        if len(blocks) < 2:
            return blocks[-1].difficulty if blocks else 4
            
        # Get actual timespan
        actual_timespan = blocks[-1].timestamp - blocks[-2016].timestamp
        
        # Limit adjustment
        if actual_timespan < target_timespan / 4:
            actual_timespan = target_timespan / 4
        if actual_timespan > target_timespan * 4:
            actual_timespan = target_timespan * 4
            
        # Calculate new difficulty
        current_target = ProofOfWork.calculate_target(blocks[-1].difficulty)
        new_target = current_target * actual_timespan // target_timespan
        
        # Convert back to difficulty
        # difficulty = 256 - log2(target)
        import math
        new_difficulty = 256 - int(math.log2(new_target))
        
        return max(1, new_difficulty)
