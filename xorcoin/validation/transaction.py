"""
Transaction validation for Xorcoin
"""

import time
from typing import List
from ..core.models import Transaction
from ..core.utxo import UTXOSet
from ..crypto.keys import KeyManager
from cryptography.hazmat.backends import default_backend
from ..crypto.signatures import SignatureManager
from cryptography.hazmat.primitives import serialization


class TransactionValidator:
    """Validates Xorcoin transactions"""
    
    def __init__(self, utxo_set: UTXOSet, mempool: List[Transaction]):
        self.utxo_set = utxo_set
        self.mempool = mempool
        
    def validate_transaction(self, tx: Transaction) -> bool:
        """
        Validate a transaction
        
        Args:
            tx: Transaction to validate
            
        Returns:
            True if transaction is valid, False otherwise
        """
        # Check basic transaction structure
        if not tx.inputs or not tx.outputs:
            print("Transaction must have inputs and outputs")
            return False
            
        # Check chain ID for replay protection
        if tx.chain_id != 1:  # Xorcoin mainnet chain ID
            print(f"Invalid chain ID: {tx.chain_id}")
            return False
            
        # Check locktime
        if tx.locktime and tx.locktime > int(time.time()):
            print("Transaction locktime not reached")
            return False
            
        total_input_amount = 0
        used_utxos = set()
        
        # Validate each input
        for idx, tx_input in enumerate(tx.inputs):
            utxo_id = tx_input.get_utxo_id()
            
            # Check if UTXO exists
            utxo = self.utxo_set.get_utxo(utxo_id)
            if utxo is None:
                print(f"Invalid UTXO: {utxo_id}")
                return False
                
            # Check for double-spending within this transaction
            if utxo_id in used_utxos:
                print(f"Double-spend within transaction: {utxo_id}")
                return False
            used_utxos.add(utxo_id)
            
            # Verify signature
            if not self._verify_input_signature(tx, idx, utxo.script_pubkey):
                print(f"Signature verification failed for input {idx}")
                return False
                
            # Check for double-spending in mempool
            if self._is_double_spend_in_mempool(utxo_id):
                print(f"Double-spend detected in mempool: {utxo_id}")
                return False
                
            total_input_amount += utxo.amount
            
        # Check that inputs >= outputs (allowing for fees)
        total_output_amount = sum(out.amount for out in tx.outputs)
        if total_input_amount < total_output_amount:
            print(f"Insufficient inputs: {total_input_amount} < {total_output_amount}")
            return False
            
        # Additional validation rules can be added here
        # - Check output amounts are positive
        # - Check script validity
        # - Check transaction size limits
        
        return True
        
    def _verify_input_signature(self, tx: Transaction, input_index: int, expected_address: str) -> bool:
        """Verify the signature for a specific input"""
        tx_input = tx.inputs[input_index]
        
        if not tx_input.signature or not tx_input.pubkey:
            return False
            
        try:
            # Load public key from bytes
            public_key = serialization.load_pem_public_key(
                tx_input.pubkey,
                backend=default_backend()
            )
            
            # Check that public key matches expected address
            address = KeyManager.pubkey_to_address(public_key)
            if address != expected_address:
                print(f"Public key doesn't match UTXO address")
                return False
                
            # Verify signature
            message = tx.serialize_for_signing(input_index)
            return SignatureManager.verify_signature(
                public_key,
                tx_input.signature,
                message
            )
            
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
            
    def _is_double_spend_in_mempool(self, utxo_id: str) -> bool:
        """Check if UTXO is already being spent in mempool"""
        for pending_tx in self.mempool:
            for pending_input in pending_tx.inputs:
                if pending_input.get_utxo_id() == utxo_id:
                    return True
        return False
        
    def calculate_transaction_fee(self, tx: Transaction) -> int:
        """Calculate the fee for a transaction"""
        total_input = 0
        for tx_input in tx.inputs:
            utxo = self.utxo_set.get_utxo(tx_input.get_utxo_id())
            if utxo:
                total_input += utxo.amount
                
        total_output = sum(out.amount for out in tx.outputs)
        return total_input - total_output
