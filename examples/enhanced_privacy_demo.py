#!/usr/bin/env python3
"""
Enhanced Privacy Demo - Shows privacy features + swarm coordination
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def enhanced_privacy_demo():
    print("🔒 ENHANCED XORCOIN PRIVACY DEMO")
    print("Privacy features + Swarm coordination")
    print("=" * 45)
    
    try:
        # Import your existing system and new privacy enhancements
        from xorcoin import XorcoinSystem, KeyManager
        from xorcoin.privacy.swarm_privacy import SwarmEnhancedPrivacySystem
        
        # Create enhanced privacy system
        base_system = XorcoinSystem()
        privacy_system = SwarmEnhancedPrivacySystem(base_system)
        
        print("1. Created enhanced privacy system")
        
        # Enable swarm coordination
        swarm_success = privacy_system.enable_swarm_coordination()
        if swarm_success:
            print("✅ Swarm coordination enabled")
        else:
            print("⚠️  Swarm coordination not available (using regular privacy)")
        
        # Generate wallets
        print("\n2. Generating wallets...")
        alice_private, alice_public, alice_address = privacy_system.generate_wallet()
        bob_private, bob_public, bob_address = privacy_system.generate_wallet()
        miner_private, miner_public, miner_address = privacy_system.generate_wallet()
        
        print(f"   Alice: {alice_address}")
        print(f"   Bob: {bob_address}")  
        print(f"   Miner: {miner_address}")
        
        # Mine some blocks for funding
        print("\n3. Mining blocks for funding...")
        for i in range(3):
            block = privacy_system.mine_block(miner_address, reward=50)
            if block:
                print(f"   Block {block.height} mined")
        
        miner_balance = privacy_system.get_balance(miner_address)
        print(f"   Miner balance: {miner_balance} XOR")
        
        # Demo different privacy levels
        print("\n4. Testing different privacy levels...")
        
        # Basic privacy transaction
        print("   🔓 Basic privacy transaction...")
        result1 = privacy_system.create_private_transaction(
            from_private_key=miner_private,
            to_address=alice_address,
            amount=25,
            privacy_level='basic'
        )
        if "error" in result1:
            print(f"      Error: {result1.get('error', 'unknown')}")
        print(f"      Status: {result1['status']}")
        
        # Medium privacy transaction  
        print("   🔒 Medium privacy transaction...")
        result2 = privacy_system.create_private_transaction(
            from_private_key=miner_private,
            to_address=bob_address,
            amount=30,
            privacy_level='medium'
        )
        print(f"      Status: {result2['status']}")
        
        # High privacy with swarm mixing
        print("   🔐 High privacy with swarm mixing...")
        result3 = privacy_system.create_private_transaction(
            from_private_key=miner_private,
            to_address=alice_address,
            amount=10000,  # Large amount suitable for mixing
            privacy_level='high'
        )
        print(f"      Status: {result3['status']}")
        print(f"      Swarm used: {result3['swarm_used']}")
        
        if result3['mixing_request_id']:
            print(f"      Mixing ID: {result3['mixing_request_id']}")
            
            # Check mixing status
            mix_status = privacy_system.get_mixing_status(result3['mixing_request_id'])
            print(f"      Mixing status: {mix_status.get('status', 'unknown')}")
        
        # Get privacy report
        print("\n5. Privacy system report...")
        report = privacy_system.get_privacy_report()
        
        print(f"   Swarm enabled: {report['swarm_enabled']}")
        print("   Privacy features:")
        for feature in report['privacy_features']:
            print(f"      ✅ {feature}")
        
        if 'mixing_stats' in report:
            stats = report['mixing_stats']
            print(f"   Mixing stats: {stats['pending_requests']} pending, {stats['active_rounds']} active")
        
        # Clean up
        privacy_system.disable_swarm_coordination()
        print("\n✅ Enhanced privacy demo completed!")
        
        print("\n🎯 PRIVACY LEVELS DEMONSTRATED:")
        print("🔓 Basic: Standard Xorcoin transactions")
        print("🔒 Medium: Enhanced privacy features")  
        print("🔐 High: Swarm-coordinated mixing (when available)")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    enhanced_privacy_demo()
