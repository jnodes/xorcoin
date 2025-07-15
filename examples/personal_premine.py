#!/usr/bin/env python3
"""
Xorcoin Personal Pre-mining Script
Pre-mines coins to a single wallet with secure key storage
"""

import sys
import os
import json
import time
import getpass
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xorcoin import XorcoinSystem, KeyManager
from xorcoin.crypto.keys import KeyManager as Keys


class SecureWalletStorage:
    """Secure storage for private keys"""
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_private_key(private_key, password: str) -> dict:
        """Encrypt private key with password"""
        # Generate salt
        salt = os.urandom(16)
        
        # Derive key from password
        key = SecureWalletStorage.derive_key_from_password(password, salt)
        
        # Serialize private key
        serialized_key = Keys.serialize_private_key(
            private_key, 
            password.encode()
        )
        
        # Additional encryption layer
        f = Fernet(key)
        encrypted = f.encrypt(serialized_key)
        
        return {
            'encrypted_key': base64.b64encode(encrypted).decode(),
            'salt': base64.b64encode(salt).decode()
        }
    
    @staticmethod
    def decrypt_private_key(encrypted_data: dict, password: str):
        """Decrypt private key"""
        salt = base64.b64decode(encrypted_data['salt'])
        encrypted = base64.b64decode(encrypted_data['encrypted_key'])
        
        # Derive key from password
        key = SecureWalletStorage.derive_key_from_password(password, salt)
        
        # Decrypt
        f = Fernet(key)
        serialized_key = f.decrypt(encrypted)
        
        # Load private key
        return Keys.load_private_key(serialized_key, password.encode())


class PersonalPreMiner:
    def __init__(self, output_dir="my_xorcoin_wallet"):
        self.output_dir = output_dir
        self.xorcoin = None
        self.my_wallet = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def setup_my_wallet(self):
        """Generate or load personal wallet"""
        wallet_file = os.path.join(self.output_dir, "wallet.json")
        
        if os.path.exists(wallet_file):
            # Load existing wallet
            print("Existing wallet found. Loading...")
            password = getpass.getpass("Enter wallet password: ")
            
            try:
                with open(wallet_file, 'r') as f:
                    wallet_data = json.load(f)
                
                # Decrypt private key
                private_key = SecureWalletStorage.decrypt_private_key(
                    wallet_data['encrypted_private_key'],
                    password
                )
                
                public_key = private_key.public_key()
                address = wallet_data['address']
                
                self.my_wallet = {
                    'private_key': private_key,
                    'public_key': public_key,
                    'address': address
                }
                
                print(f"Wallet loaded successfully!")
                print(f"Address: {address}")
                
            except Exception as e:
                print(f"Error loading wallet: {e}")
                print("Generating new wallet instead...")
                self.create_new_wallet()
        else:
            # Create new wallet
            self.create_new_wallet()
            
    def create_new_wallet(self):
        """Create a new wallet with password protection"""
        print("\nGenerating new Xorcoin wallet...")
        
        # Get password
        while True:
            password = getpass.getpass("Enter password for new wallet: ")
            confirm = getpass.getpass("Confirm password: ")
            
            if password == confirm:
                if len(password) < 8:
                    print("Password must be at least 8 characters!")
                    continue
                break
            else:
                print("Passwords don't match! Try again.")
        
        # Generate wallet
        private_key, public_key, address = KeyManager.generate_keypair()
        
        self.my_wallet = {
            'private_key': private_key,
            'public_key': public_key,
            'address': address
        }
        
        # Encrypt and save
        encrypted_data = SecureWalletStorage.encrypt_private_key(private_key, password)
        
        wallet_data = {
            'address': address,
            'created': datetime.now().isoformat(),
            'encrypted_private_key': encrypted_data,
            'public_key': Keys.serialize_public_key(public_key).decode()
        }
        
        wallet_file = os.path.join(self.output_dir, "wallet.json")
        with open(wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        # Also save address in plain text for easy reference
        address_file = os.path.join(self.output_dir, "address.txt")
        with open(address_file, 'w') as f:
            f.write(f"Xorcoin Address: {address}\n")
            f.write(f"Created: {datetime.now()}\n")
            f.write("\nIMPORTANT: This is your Xorcoin address, not a Bitcoin address!\n")
            f.write("Keep your wallet.json file and password safe!\n")
        
        print(f"\n✅ Wallet created successfully!")
        print(f"Address: {address}")
        print(f"Files saved to: {self.output_dir}/")
        print("\n⚠️  IMPORTANT: Remember your password! It cannot be recovered!")
        
    def initialize_xorcoin_with_my_genesis(self):
        """Initialize Xorcoin with genesis block going to my wallet"""
        print("\nInitializing Xorcoin with your wallet as genesis recipient...")
        
        # Create XorcoinSystem
        self.xorcoin = XorcoinSystem()
        
        # Override the genesis block to use my address
        genesis_tx = self.xorcoin.blockchain.chain[0].transactions[0]
        genesis_tx.outputs[0].script_pubkey = self.my_wallet['address']
        
        # Re-process genesis block to update UTXO set
        self.xorcoin.utxo_set = self.xorcoin.utxo_set.__class__()  # Reset UTXO set
        self.xorcoin._process_block(self.xorcoin.blockchain.chain[0])
        
        initial_balance = self.xorcoin.get_balance(self.my_wallet['address'])
        print(f"Genesis block created with {initial_balance:,} XOR to your address")
        
    def premine_blocks(self, num_blocks=50, reward_per_block=50):
        """Pre-mine all blocks to my wallet"""
        print(f"\nPre-mining {num_blocks} blocks to your wallet...")
        print(f"Reward per block: {reward_per_block} XOR")
        
        my_address = self.my_wallet['address']
        start_time = time.time()
        
        for i in range(num_blocks):
            print(f"\nMining block {i+1}/{num_blocks}...")
            block_start = time.time()
            
            block = self.xorcoin.mine_block(my_address, reward=reward_per_block)
            
            if block:
                block_time = time.time() - block_start
                total_elapsed = time.time() - start_time
                avg_time = total_elapsed / (i + 1)
                eta = avg_time * (num_blocks - i - 1)
                
                print(f"✓ Block {block.height} mined in {block_time:.2f}s")
                print(f"  Hash: {block.get_header_hash()[:32]}...")
                print(f"  Progress: {((i+1)/num_blocks)*100:.1f}%")
                print(f"  ETA: {eta/60:.1f} minutes")
                
                # Show balance periodically
                if (i + 1) % 10 == 0:
                    balance = self.xorcoin.get_balance(my_address)
                    print(f"  Current balance: {balance:,} XOR")
                    
        print("\n✅ Pre-mining complete!")
        
    def save_blockchain_backup(self):
        """Save blockchain data for backup"""
        backup_dir = os.path.join(self.output_dir, "blockchain_backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save blockchain data
        blockchain_data = []
        for block in self.xorcoin.blockchain.chain:
            block_info = {
                'height': block.height,
                'hash': block.get_header_hash(),
                'timestamp': block.timestamp,
                'difficulty': block.difficulty,
                'nonce': block.nonce,
                'num_transactions': len(block.transactions)
            }
            blockchain_data.append(block_info)
            
        backup_file = os.path.join(backup_dir, f"blockchain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(blockchain_data, f, indent=2)
            
        print(f"Blockchain backup saved to: {backup_file}")
        
    def generate_summary_report(self):
        """Generate a summary report of pre-mining"""
        report_file = os.path.join(self.output_dir, "premine_report.txt")
        
        my_address = self.my_wallet['address']
        final_balance = self.xorcoin.get_balance(my_address)
        blockchain_info = self.xorcoin.get_blockchain_info()
        
        report = f"""
XORCOIN PRE-MINING REPORT
========================
Generated: {datetime.now()}

Wallet Information:
------------------
Address: {my_address}
Balance: {final_balance:,} XOR

Blockchain Statistics:
---------------------
Height: {blockchain_info['height']}
Latest Hash: {blockchain_info['latest_hash']}
Difficulty: {blockchain_info['difficulty']}
Total Blocks: {len(self.xorcoin.blockchain.chain)}
UTXO Count: {blockchain_info['utxo_count']}

Genesis Block:
-------------
Hash: {self.xorcoin.blockchain.chain[0].get_header_hash()}
Initial Supply: 1,000,000 XOR

Mining Summary:
--------------
Blocks Mined: {len(self.xorcoin.blockchain.chain) - 1}
Mining Rewards: {(len(self.xorcoin.blockchain.chain) - 1) * 50:,} XOR
Total Supply: {final_balance:,} XOR

Files Created:
-------------
- wallet.json (encrypted private key)
- address.txt (your Xorcoin address)
- premine_report.txt (this file)
- blockchain_backup/ (blockchain data)

IMPORTANT REMINDERS:
-------------------
1. Your Xorcoin address is NOT a Bitcoin address
2. Keep wallet.json and your password secure
3. Back up your wallet files regularly
4. This is a separate blockchain from Bitcoin

To use your coins:
-----------------
1. Run the Xorcoin node software
2. Import your wallet using wallet.json
3. Create transactions using your private key
"""
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"\nReport saved to: {report_file}")
        
        # Also display key information
        print("\n" + "="*60)
        print("PRE-MINING COMPLETE!")
        print("="*60)
        print(f"Your Xorcoin Address: {my_address}")
        print(f"Final Balance: {final_balance:,} XOR")
        print(f"Blockchain Height: {blockchain_info['height']}")
        print(f"\nFiles saved to: {self.output_dir}/")
        print("\n⚠️  IMPORTANT: This is a Xorcoin address, NOT a Bitcoin address!")


def main():
    # Configuration
    NUM_BLOCKS = 100  # Number of blocks to pre-mine
    BLOCK_REWARD = 50  # Reward per block
    
    print("=== Xorcoin Personal Pre-mining ===\n")
    print("This will create a Xorcoin wallet and pre-mine coins to it.")
    print("Note: Xorcoin addresses are different from Bitcoin addresses!\n")
    
    # Create pre-miner
    preminer = PersonalPreMiner()
    
    # Setup wallet (create new or load existing)
    preminer.setup_my_wallet()
    
    # Initialize blockchain with genesis going to my wallet
    preminer.initialize_xorcoin_with_my_genesis()
    
    # Pre-mine blocks
    preminer.premine_blocks(NUM_BLOCKS, BLOCK_REWARD)
    
    # Save backup
    preminer.save_blockchain_backup()
    
    # Generate report
    preminer.generate_summary_report()
    
    print("\n✅ All done! Check your wallet directory for all files.")


if __name__ == "__main__":
    main()
