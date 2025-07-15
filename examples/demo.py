#!/usr/bin/env python3
"""
Xorcoin Demo - Shows basic usage of the Xorcoin system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xorcoin import XorcoinSystem, KeyManager


def main():
    print("=== Xorcoin Demo ===\n")
    
    # Initialize Xorcoin system
    print("Initializing Xorcoin system...")
    xorcoin = XorcoinSystem()
    
    # Show blockchain info
    info = xorcoin.get_blockchain_info()
    print(f"\nBlockchain Info:")
    print(f"  Height: {info['height']}")
    print(f"  Latest Hash: {info['latest_hash'][:16]}...")
    print(f"  Difficulty: {info['difficulty']}")
    print(f"  UTXO Count: {info['utxo_count']}")
    
    # Generate wallets
    print("\n--- Generating Wallets ---")
    
    # Alice's wallet
    alice_private, alice_public, alice_address = xorcoin.generate_wallet()
    print(f"Alice's address: {alice_address}")
    
    # Bob's wallet
    bob_private, bob_public, bob_address = xorcoin.generate_wallet()
    print(f"Bob's address: {bob_address}")
    
    # Miner's wallet
    miner_private, miner_public, miner_address = xorcoin.generate_wallet()
    print(f"Miner's address: {miner_address}")
    
    # Check initial balances
    print("\n--- Initial Balances ---")
    print(f"Alice: {xorcoin.get_balance(alice_address)} XOR")
    print(f"Bob: {xorcoin.get_balance(bob_address)} XOR")
    print(f"Miner: {xorcoin.get_balance(miner_address)} XOR")
    
    # Mine first block to get some coins
    print("\n--- Mining Block 1 ---")
    block1 = xorcoin.mine_block(miner_address, reward=50)
    if block1:
        print(f"Block mined! Height: {block1.height}, Hash: {block1.get_header_hash()[:16]}...")
        print(f"Miner balance: {xorcoin.get_balance(miner_address)} XOR")
    
    # Create transaction from miner to Alice
    print("\n--- Creating Transaction: Miner -> Alice (30 XOR) ---")
    tx1 = xorcoin.create_transaction(
        from_address=miner_address,
        to_address=alice_address,
        amount=30,
        private_key=miner_private
    )
    
    if tx1:
        print(f"Transaction created: {tx1.get_hash()[:16]}...")
        if xorcoin.add_transaction(tx1):
            print("Transaction added to mempool")
    
    # Mine second block to confirm transaction
    print("\n--- Mining Block 2 ---")
    block2 = xorcoin.mine_block(miner_address, reward=50)
    if block2:
        print(f"Block mined! Height: {block2.height}")
        print(f"Transactions in block: {len(block2.transactions)}")
    
    # Check balances after transaction
    print("\n--- Updated Balances ---")
    print(f"Alice: {xorcoin.get_balance(alice_address)} XOR")
    print(f"Bob: {xorcoin.get_balance(bob_address)} XOR")
    print(f"Miner: {xorcoin.get_balance(miner_address)} XOR")
    
    # Create transaction from Alice to Bob
    print("\n--- Creating Transaction: Alice -> Bob (10 XOR) ---")
    tx2 = xorcoin.create_transaction(
        from_address=alice_address,
        to_address=bob_address,
        amount=10,
        private_key=alice_private
    )
    
    if tx2:
        print(f"Transaction created: {tx2.get_hash()[:16]}...")
        if xorcoin.add_transaction(tx2):
            print("Transaction added to mempool")
    
    # Mine third block
    print("\n--- Mining Block 3 ---")
    block3 = xorcoin.mine_block(miner_address, reward=50)
    if block3:
        print(f"Block mined! Height: {block3.height}")
    
    # Final balances
    print("\n--- Final Balances ---")
    print(f"Alice: {xorcoin.get_balance(alice_address)} XOR")
    print(f"Bob: {xorcoin.get_balance(bob_address)} XOR")
    print(f"Miner: {xorcoin.get_balance(miner_address)} XOR")
    
    # Show final blockchain info
    info = xorcoin.get_blockchain_info()
    print(f"\n--- Final Blockchain Info ---")
    print(f"  Height: {info['height']}")
    print(f"  Mempool Size: {info['mempool_size']}")
    print(f"  UTXO Count: {info['utxo_count']}")
    
    # Validate blockchain
    print("\n--- Validating Blockchain ---")
    is_valid = xorcoin.blockchain.validate_chain()
    print(f"Blockchain valid: {is_valid}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
