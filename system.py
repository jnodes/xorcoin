"""
Main Xorcoin system implementation
"""

from typing import List, Dict, Tuple, Optional
from .core import (
    UTXO, TxInput, TxOutput, Transaction, Block,
    UTXOSet, BlockMiner, Blockchain
)
from .crypto import KeyManager, SignatureManager
from .validation import TransactionValidator
from .network import XorcoinServer
from cryptography.hazmat.primitives.asymmetric import ec


class XorcoinSystem:
    """Main Xorcoin system coordinating all components"""
    
    def __init__(self):
        self.utxo_set = UTXOSet()
        self.mempool: List[Transaction] = []
        self.confirmed_txs: Dict[str, Transaction] = {}
        self.blockchain = Blockchain()
        self.key_manager = KeyManager()
        self.server: Optional[XorcoinServer] = None
        
        # Initialize with genesis block
        self._create_genesis_block()
        
    def _create_genesis_block(self) -> None:
        """Create the genesis block with initial coin distribution"""
        # Create genesis transaction (coinbase)
        genesis_tx = Transaction(
            version=1,
            chain_id=1,
            inputs=[],  # No inputs for coinbase
            outputs=[
                TxOutput(
                    amount=1000000,  # 1M Xorcoin initial supply
                    script_pubkey="genesis"  # Special genesis address
                )
            ]
        )
        
        # Create genesis block
        genesis_block = Block(
            height=0,
            prev_block_hash="0" * 64,
            transactions=[genesis_tx]
        )
        
        # Mine genesis block
        BlockMiner.mine_block(genesis_block, target_difficulty=4)
        self.blockchain.chain.append(genesis_block)
        
        # Process genesis block to create initial UTXO
        self._process_block(genesis_block)
        
    def generate_wallet(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey, str]:
        """Generate a new wallet (keypair and address)"""
        return self.key_manager.generate_keypair()
        
    def get_balance(self, address: str) -> int:
        """Get balance for an address"""
        return self.utxo_set.get_balance(address)
        
    def create_transaction(
        self,
        from_address: str,
        to_address: str,
        amount: int,
        private_key: ec.EllipticCurvePrivateKey
    ) -> Optional[Transaction]:
        """
        Create a new transaction
        
        Args:
            from_address: Sender's address
            to_address: Recipient's address
            amount: Amount to send
            private_key: Sender's private key for signing
            
        Returns:
            Transaction object if successful, None otherwise
        """
        # Get UTXOs for sender
        sender_utxos = self.utxo_set.get_utxos_for_address(from_address)
        
        if not sender_utxos:
            print("No UTXOs found for sender")
            return None
            
        # Select UTXOs to spend
        selected_utxos = []
        total_input = 0
        
        for utxo_id, utxo in sender_utxos.items():
            selected_utxos.append((utxo_id, utxo))
            total_input += utxo.amount
            if total_input >= amount:
                break
                
        if total_input < amount:
            print(f"Insufficient balance: {total_input} < {amount}")
            return None
            
        # Create transaction
        tx = Transaction(version=2, chain_id=1)
        
        # Add inputs
        for utxo_id, utxo in selected_utxos:
            tx_input = TxInput(
                prev_tx_hash=utxo.tx_hash,
                prev_output_index=utxo.output_index
            )
            tx.inputs.append(tx_input)
            
        # Add outputs
        tx.outputs.append(TxOutput(amount=amount, script_pubkey=to_address))
        
        # Add change output if necessary
        change = total_input - amount
        if change > 0:
            tx.outputs.append(TxOutput(amount=change, script_pubkey=from_address))
            
        # Sign inputs
        public_key = private_key.public_key()
        pub_key_bytes = self.key_manager.serialize_public_key(public_key)
        
        for i, tx_input in enumerate(tx.inputs):
            message = tx.serialize_for_signing(i)
            signature = SignatureManager.sign_message(private_key, message)
            tx_input.signature = signature
            tx_input.pubkey = pub_key_bytes
            
        return tx
        
    def add_transaction(self, tx: Transaction) -> bool:
        """Validate and add transaction to mempool"""
        validator = TransactionValidator(self.utxo_set, self.mempool)
        
        if validator.validate_transaction(tx):
            self.mempool.append(tx)
            print(f"Transaction {tx.get_hash()} added to mempool")
            return True
        else:
            print("Transaction validation failed")
            return False
            
    def mine_block(self, miner_address: str, reward: int = 50) -> Optional[Block]:
        """
        Mine a new block
        
        Args:
            miner_address: Address to receive mining reward
            reward: Mining reward amount
            
        Returns:
            Mined block if successful
        """
        # Create coinbase transaction
        coinbase_tx = Transaction(
            version=1,
            chain_id=1,
            inputs=[],  # No inputs for coinbase
            outputs=[
                TxOutput(amount=reward, script_pubkey=miner_address)
            ]
        )
        
        # Create new block with pending transactions
        block = Block(
            transactions=[coinbase_tx] + self.mempool[:10]  # Limit block size
        )
        
        # Add block to blockchain
        if self.blockchain.add_block(block):
            # Process block
            self._process_block(block)
            
            # Clear processed transactions from mempool
            for tx in block.transactions[1:]:  # Skip coinbase
                if tx in self.mempool:
                    self.mempool.remove(tx)
                    
            return block
            
        return None
        
    def _process_block(self, block: Block) -> None:
        """Process all transactions in a block"""
        for tx in block.transactions:
            # Skip validation for coinbase transactions
            if tx.inputs:
                # Remove spent UTXOs
                for inp in tx.inputs:
                    utxo_id = inp.get_utxo_id()
                    self.utxo_set.remove_utxo(utxo_id)
                    
            # Add new UTXOs
            tx_hash = tx.get_hash()
            for idx, out in enumerate(tx.outputs):
                utxo = UTXO(
                    tx_hash=tx_hash,
                    output_index=idx,
                    amount=out.amount,
                    script_pubkey=out.script_pubkey
                )
                self.utxo_set.add_utxo(utxo)
                
            # Store confirmed transaction
            self.confirmed_txs[tx_hash] = tx
            
        print(f"Block {block.height} processed with {len(block.transactions)} transactions")
        
    def start_server(self, host: str = '0.0.0.0', port: int = 8443,
                    certfile: str = 'cert.pem', keyfile: str = 'key.pem') -> None:
        """Start the Xorcoin network server"""
        self.server = XorcoinServer(host, port)
        self.server.setup_ssl(certfile, keyfile)
        
        # Set message handler
        self.server.set_message_handler(self._handle_network_message)
        
        self.server.start()
        
    def _handle_network_message(self, message: dict) -> dict:
        """Handle incoming network messages"""
        msg_type = message.get('type')
        
        if msg_type == 'ping':
            return {"status": "ok", "message": "pong"}
        elif msg_type == 'get_balance':
            address = message.get('address')
            balance = self.get_balance(address)
            return {"status": "ok", "balance": balance}
        elif msg_type == 'submit_transaction':
            # Handle transaction submission
            # This would need proper deserialization
            return {"status": "ok", "message": "Transaction received"}
        else:
            return {"status": "error", "message": "Unknown message type"}
            
    def get_blockchain_info(self) -> dict:
        """Get information about the blockchain"""
        latest_block = self.blockchain.get_latest_block()
        return {
            "height": len(self.blockchain.chain),
            "latest_hash": latest_block.get_header_hash(),
            "difficulty": latest_block.difficulty,
            "mempool_size": len(self.mempool),
            "utxo_count": len(self.utxo_set)
        }
