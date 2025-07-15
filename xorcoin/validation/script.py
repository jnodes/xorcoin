"""
Script validation with security limits
"""
from typing import Optional

class ScriptValidator:
    """Validates transaction scripts with security limits"""
    
    # Security limits
    MAX_SCRIPT_SIZE = 10000
    MAX_SCRIPT_ELEMENT_SIZE = 520
    MAX_OPS_PER_SCRIPT = 201
    MAX_PUBKEYS_PER_MULTISIG = 20
    MAX_STACK_SIZE = 1000
    MAX_SCRIPT_NUM_LENGTH = 4  # 32-bit integers
    
    @staticmethod
    def validate_script_size(script: str) -> bool:
        """Check script doesn't exceed size limits"""
        return len(script.encode()) <= ScriptValidator.MAX_SCRIPT_SIZE
        
    @staticmethod
    def validate_script_pubkey(script_pubkey: str) -> bool:
        """Validate output script"""
        if not script_pubkey:
            return False
            
        # Check size
        if not ScriptValidator.validate_script_size(script_pubkey):
            return False
            
        # In real implementation, would parse and validate script operations
        # For now, just check it's a valid hex string (simplified)
        try:
            int(script_pubkey, 16)
            return True
        except ValueError:
            # Not hex, might be address format
            return len(script_pubkey) == 40  # RIPEMD160 hash length
            
    @staticmethod
    def count_sigops(script: str) -> int:
        """Count signature operations in script"""
        # Simplified - real implementation would parse script
        # and count OP_CHECKSIG, OP_CHECKSIGVERIFY, etc.
        return 1  # Assume standard transaction
