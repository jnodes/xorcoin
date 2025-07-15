"""
Fork choice rules for handling blockchain forks
"""
from typing import List, Dict
from xorcoin.core.models import Block, Transaction, Transaction, Transaction

class ForkChoice:
    @staticmethod
    def get_canonical_chain(chains: Dict[str, List[Block]]) -> List[Block]:
        """
        Implement longest chain rule with most work
        """
        best_chain = None
        best_work = 0
        
        for chain_id, chain in chains.items():
            total_work = sum(2 ** block.difficulty for block in chain)
            if total_work > best_work:
                best_work = total_work
                best_chain = chain
                
        return best_chain
    
    @staticmethod
    def handle_reorg(old_chain: List[Block], new_chain: List[Block]) -> List[Transaction]:
        """
        Handle chain reorganization
        Returns list of transactions to re-add to mempool
        """
        # Find common ancestor
        common_height = 0
        for i in range(min(len(old_chain), len(new_chain))):
            if old_chain[i].get_header_hash() != new_chain[i].get_header_hash():
                common_height = i
                break
                
        # Get transactions from removed blocks
        removed_txs = []
        for block in old_chain[common_height:]:
            removed_txs.extend(block.transactions[1:])  # Skip coinbase
            
        return removed_txs
