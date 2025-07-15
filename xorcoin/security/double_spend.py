"""
Enhanced double-spend protection
"""
import threading
from typing import Set, Dict
from xorcoin.core.models import Transaction

class DoubleSpendProtector:
    def __init__(self):
        self.spent_utxos: Set[str] = set()
        self.pending_utxos: Dict[str, Transaction] = {}
        self.lock = threading.RLock()
        
    def check_and_lock_utxos(self, tx: Transaction) -> bool:
        """Atomically check and lock UTXOs"""
        with self.lock:
            # Check if any input is already spent
            for inp in tx.inputs:
                utxo_id = inp.get_utxo_id()
                if utxo_id in self.spent_utxos or utxo_id in self.pending_utxos:
                    return False
                    
            # Lock all UTXOs
            for inp in tx.inputs:
                utxo_id = inp.get_utxo_id()
                self.pending_utxos[utxo_id] = tx
                
            return True
            
    def commit_transaction(self, tx: Transaction):
        """Mark UTXOs as permanently spent"""
        with self.lock:
            for inp in tx.inputs:
                utxo_id = inp.get_utxo_id()
                self.pending_utxos.pop(utxo_id, None)
                self.spent_utxos.add(utxo_id)
                
    def rollback_transaction(self, tx: Transaction):
        """Release UTXO locks"""
        with self.lock:
            for inp in tx.inputs:
                utxo_id = inp.get_utxo_id()
                self.pending_utxos.pop(utxo_id, None)
