"""
Enhanced mempool with size limits and fee prioritization
"""
import heapq
from typing import List, Dict, Optional
from xorcoin.core.models import Transaction

class Mempool:
    def __init__(self, max_size: int = 300_000_000):  # 300MB default
        self.transactions: Dict[str, Transaction] = {}
        self.tx_by_fee: List[tuple] = []  # Min heap of (-fee_per_byte, tx_hash)
        self.current_size = 0
        self.max_size = max_size
        self.min_fee_rate = 0.001  # Satoshis per byte (lowered for demo)
        
    def add_transaction(self, tx: Transaction, fee: int) -> bool:
        """Add transaction with fee-based prioritization"""
        tx_hash = tx.get_hash()
        tx_size = len(str(tx).encode())
        fee_rate = fee / tx_size
        
        # Check minimum fee
        if fee_rate < self.min_fee_rate:
            return False
            
        # Check if mempool is full
        if self.current_size + tx_size > self.max_size:
            # Try to evict lower fee transactions
            if not self._make_room(tx_size, fee_rate):
                return False
                
        # Add transaction
        self.transactions[tx_hash] = tx
        heapq.heappush(self.tx_by_fee, (-fee_rate, tx_hash))
        self.current_size += tx_size
        
        return True
        
    def _make_room(self, needed_size: int, new_fee_rate: float) -> bool:
        """Evict low-fee transactions to make room"""
        evicted_size = 0
        to_evict = []
        
        # Find transactions with lower fee rate
        temp_heap = []
        while self.tx_by_fee and evicted_size < needed_size:
            neg_fee_rate, tx_hash = heapq.heappop(self.tx_by_fee)
            fee_rate = -neg_fee_rate
            
            if fee_rate < new_fee_rate:
                to_evict.append(tx_hash)
                if tx_hash in self.transactions:
                    tx = self.transactions[tx_hash]
                    evicted_size += len(str(tx).encode())
            else:
                temp_heap.append((neg_fee_rate, tx_hash))
                
        # Restore heap
        for item in temp_heap:
            heapq.heappush(self.tx_by_fee, item)
            
        # Evict if we can make enough room
        if evicted_size >= needed_size:
            for tx_hash in to_evict:
                if tx_hash in self.transactions:
                    del self.transactions[tx_hash]
            return True
            
        return False
        
    def get_transactions_for_block(self, max_block_size: int) -> List[Transaction]:
        """Get highest fee transactions for block"""
        selected = []
        current_size = 0
        
        # Sort by fee rate
        sorted_txs = sorted(
            self.tx_by_fee,
            key=lambda x: x[0]  # Negative fee rate
        )
        
        for neg_fee_rate, tx_hash in sorted_txs:
            tx = self.transactions.get(tx_hash)
            if not tx:
                continue
                
            tx_size = len(str(tx).encode())
            if current_size + tx_size <= max_block_size:
                selected.append(tx)
                current_size += tx_size
            else:
                break
                
        return selected

    def __len__(self) -> int:
        """Return number of transactions in mempool"""
        return len(self.transactions)
