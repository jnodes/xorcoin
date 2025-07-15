"""
UTXO Set Management for Xorcoin
"""

from typing import Dict, Optional
from .models import UTXO


class UTXOSet:
    """Manages the set of unspent transaction outputs"""
    
    def __init__(self):
        self.utxos: Dict[str, UTXO] = {}

    def add_utxo(self, utxo: UTXO) -> None:
        """Add a new UTXO to the set"""
        self.utxos[utxo.get_id()] = utxo

    def remove_utxo(self, utxo_id: str) -> None:
        """Remove a spent UTXO from the set"""
        if utxo_id in self.utxos:
            del self.utxos[utxo_id]

    def get_utxo(self, utxo_id: str) -> Optional[UTXO]:
        """Get a UTXO by its ID"""
        return self.utxos.get(utxo_id)

    def get_balance(self, address: str) -> int:
        """Get the balance for a given address (pubkey hash)"""
        return sum(
            utxo.amount 
            for utxo in self.utxos.values() 
            if utxo.script_pubkey == address
        )

    def get_utxos_for_address(self, address: str) -> Dict[str, UTXO]:
        """Get all UTXOs for a given address"""
        return {
            utxo_id: utxo
            for utxo_id, utxo in self.utxos.items()
            if utxo.script_pubkey == address
        }

    def __len__(self) -> int:
        """Get the number of UTXOs in the set"""
        return len(self.utxos)

    def __contains__(self, utxo_id: str) -> bool:
        """Check if a UTXO exists in the set"""
        return utxo_id in self.utxos
