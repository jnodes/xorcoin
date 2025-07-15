"""
Thread-safe UTXO set implementation
"""
import threading
from typing import Dict, Optional
from xorcoin.core.models import UTXO

class ThreadSafeUTXOSet:
    """Thread-safe UTXO set management"""
    
    def __init__(self):
        self.utxos: Dict[str, UTXO] = {}
        self.lock = RWLock()  # Read-write lock for better performance
        
    def add_utxo(self, utxo: UTXO) -> None:
        """Add a new UTXO to the set"""
        with self.lock.write():
            self.utxos[utxo.get_id()] = utxo
            
    def remove_utxo(self, utxo_id: str) -> bool:
        """Remove a spent UTXO from the set"""
        with self.lock.write():
            if utxo_id in self.utxos:
                del self.utxos[utxo_id]
                return True
            return False
            
    def get_utxo(self, utxo_id: str) -> Optional[UTXO]:
        """Get a UTXO by its ID"""
        with self.lock.read():
            return self.utxos.get(utxo_id)
            
    def get_balance(self, address: str) -> int:
        """Get the balance for a given address"""
        with self.lock.read():
            return sum(
                utxo.amount 
                for utxo in self.utxos.values() 
                if utxo.script_pubkey == address
            )
            
    def get_utxos_for_address(self, address: str) -> Dict[str, UTXO]:
        """Get all UTXOs for a given address"""
        with self.lock.read():
            return {
                utxo_id: utxo
                for utxo_id, utxo in self.utxos.items()
                if utxo.script_pubkey == address
            }
            
    def batch_update(self, to_add: list[UTXO], to_remove: list[str]) -> None:
        """Atomically add and remove multiple UTXOs"""
        with self.lock.write():
            # Remove first to free memory
            for utxo_id in to_remove:
                self.utxos.pop(utxo_id, None)
                
            # Then add new ones
            for utxo in to_add:
                self.utxos[utxo.get_id()] = utxo

    def __len__(self) -> int:
        """Return the number of UTXOs in the set"""
        with self.lock.read():
            return len(self.utxos)

    def __contains__(self, utxo_id: str) -> bool:
        """Check if a UTXO exists in the set"""
        with self.lock.read():
            return utxo_id in self.utxos


class RWLock:
    """Simple read-write lock implementation"""
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        
    def read(self):
        """Acquire read lock"""
        return self._ReadLock(self)
        
    def write(self):
        """Acquire write lock"""
        return self._WriteLock(self)
        
    class _ReadLock:
        def __init__(self, rwlock):
            self.rwlock = rwlock
            
        def __enter__(self):
            self.rwlock._read_ready.acquire()
            self.rwlock._readers += 1
            self.rwlock._read_ready.release()
            
        def __exit__(self, *args):
            self.rwlock._read_ready.acquire()
            self.rwlock._readers -= 1
            if self.rwlock._readers == 0:
                self.rwlock._read_ready.notifyAll()
            self.rwlock._read_ready.release()
            
    class _WriteLock:
        def __init__(self, rwlock):
            self.rwlock = rwlock
            
        def __enter__(self):
            self.rwlock._read_ready.acquire()
            while self.rwlock._readers > 0:
                self.rwlock._read_ready.wait()
                
        def __exit__(self, *args):
            self.rwlock._read_ready.release()
