"""
Xorcoin validation components
"""

# Direct imports that don't cause circular dependencies
from .transaction import TransactionValidator
from .script import ScriptValidator

# Lazy import for BlockValidator to avoid circular dependencies
_block_validator = None

def get_block_validator():
    global _block_validator
    if _block_validator is None:
        from .block import BlockValidator
        _block_validator = BlockValidator
    return _block_validator

__all__ = [
    "TransactionValidator",
    "ScriptValidator",
    "get_block_validator",
]
