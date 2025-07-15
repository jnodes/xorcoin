"""
Xorcoin - A minimalistic secure UTXO-based token system
"""

from .system import XorcoinSystem
from .core.models import Transaction, Block, UTXO, TxInput, TxOutput
from .crypto.keys import KeyManager

__version__ = "0.1.0"
__all__ = [
    "XorcoinSystem",
    "Transaction",
    "Block",
    "UTXO",
    "TxInput",
    "TxOutput",
    "KeyManager",
]
