"""
Main Xorcoin system implementation
"""

from typing import List, Dict, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import ec
import yaml

from xorcoin.economics import XorcoinEconomics
# Core imports
from xorcoin.core import (
    UTXO, TxInput, TxOutput, Transaction, Block,
    BlockMiner, Blockchain
)
from xorcoin.core.utxo_threadsafe import ThreadSafeUTXOSet
from xorcoin.core.mempool import Mempool

# Security imports
from xorcoin.security import DoubleSpendProtector, RateLimiter, BanManager

# Consensus imports
from xorcoin.consensus import ConsensusRules, ForkChoice

# Crypto imports
from xorcoin.crypto import KeyManager, SignatureManager

# Validation imports
from xorcoin.validation import TransactionValidator

# Network imports
from xorcoin.network import XorcoinServer


class XorcoinSystem:
    """Main Xorcoin system coordinating all components"""
    
    def __init__(self):
        # Core components
        self.utxo_set = ThreadSafeUTXOSet()
        self.mempool = Mempool()
        self.confirmed_txs: Dict[str, Transaction] = {}
        self.blockchain = Blockchain()
        self.key_manager = KeyManager()
        self.server: Optional[XorcoinServer] = None
        
        # Security components
        self.double_spend_protector = DoubleSpendProtector()
        self.rate_limiter = RateLimiter()
        self.ban_manager = BanManager()
        
        # Load security config
        try:
            with open('config/security.yaml', 'r') as f:
                self.security_config = yaml.safe_load(f)
        except FileNotFoundError:
            print("Warning: security.yaml not found, using defaults")
            self.security_config = {}
        
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
                    amount=XorcoinEconomics.get_block_reward(0),  # Use economics-defined amount
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
        
    def calculate_min_fee(self, tx: Transaction) -> int:
        """Calculate minimum fee for a transaction based on size"""
        tx_size = len(str(tx).encode())
        min_fee_rate = self.mempool.min_fee_rate
        return tx_size * min_fee_rate

    def calculate_min_fee(self, tx: Transaction) -> int:
        """Calculate minimum fee for a transaction based on size"""
        tx_size = len(str(tx).encode())
        min_fee_rate = self.mempool.min_fee_rate
        return tx_size * min_fee_rate

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
        
        # Calculate minimum fee
        min_fee = len(str(tx).encode()) * self.mempool.min_fee_rate
        
        # Add change output if necessary (minus fee)
        change = total_input - amount - min_fee
        if change > 0:
            tx.outputs.append(TxOutput(amount=change, script_pubkey=from_address))
        elif change < 0:
            print(f"Insufficient balance for transaction fee: need {min_fee} additional")
            return None
            
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
        """Validate and add transaction to mempool with security checks"""
        # First check double-spend protection
        if not self.double_spend_protector.check_and_lock_utxos(tx):
            print("Transaction rejected: double-spend attempt")
            return False
            
        # Validate transaction
        validator = TransactionValidator(self.utxo_set, list(self.mempool.transactions.values()))
        
        if validator.validate_transaction(tx):
            # Calculate fee
            fee = validator.calculate_transaction_fee(tx)
            
            # Try to add to enhanced mempool
            if self.mempool.add_transaction(tx, fee):
                print(f"Transaction {tx.get_hash()} added to mempool")
                return True
            else:
                print("Transaction rejected: mempool full or fee too low")
                # Rollback UTXO locks
                self.double_spend_protector.rollback_transaction(tx)
                return False
        else:
            print("Transaction validation failed")
            # Rollback UTXO locks
            self.double_spend_protector.rollback_transaction(tx)
            return False
            
    def mine_block(self, miner_address: str, reward: int = 50) -> Optional[Block]:
        """
        Mine a new block
        
        Args:
            miner_address: Address to receive mining reward
            reward: Mining reward amount (will be overridden by economics)
            
        Returns:
            Mined block if successful
        """
        # Get proper reward from economics
        current_height = len(self.blockchain.chain)
        actual_reward = XorcoinEconomics.get_block_reward(current_height)
        
        # Create coinbase transaction
        coinbase_tx = Transaction(
            version=1,
            chain_id=1,
            inputs=[],  # No inputs for coinbase
            outputs=[
                TxOutput(amount=actual_reward, script_pubkey=miner_address)
            ]
        )
        
        # Create new block with pending transactions
        block = Block(
            transactions=[coinbase_tx] + list(self.mempool.transactions.values())[:10]  # Limit block size
        )
        
        # Add block to blockchain
        if self.blockchain.add_block(block):
            # Process block
            self._process_block(block)
            
            # Clear processed transactions from mempool
            for tx in block.transactions[1:]:  # Skip coinbase
                if tx.get_hash() in self.mempool.transactions:
                    del self.mempool.transactions[tx.get_hash()]
                    
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
        """Get information about the blockchain with economics data"""
        latest_block = self.blockchain.get_latest_block()
        current_height = len(self.blockchain.chain)
        
        # Get economics info
        current_reward = XorcoinEconomics.get_block_reward(current_height)
        total_supply = XorcoinEconomics.get_total_supply_at_height(current_height)
        blocks_until_halving = XorcoinEconomics.HALVING_INTERVAL - (current_height % XorcoinEconomics.HALVING_INTERVAL)
        
        return {
            "height": current_height,
            "latest_hash": latest_block.get_header_hash(),
            "difficulty": latest_block.difficulty,
            "mempool_size": len(self.mempool.transactions),
            "utxo_count": len(self.utxo_set),
            "current_reward": current_reward,
            "total_supply": total_supply,
            "blocks_until_halving": blocks_until_halving,
            "max_supply": XorcoinEconomics.MAX_SUPPLY
        }
