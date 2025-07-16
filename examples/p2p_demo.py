#!/usr/bin/env python3
"""
Xorcoin P2P Network Demo
"""

import sys
import os
import time
from typing import Optional
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xorcoin import XorcoinSystem
from xorcoin.network.p2p import P2PNode


def run_node(port: int, bootstrap_peer: Optional[tuple] = None):
    """Run a P2P node"""
    print(f"\n=== Starting Xorcoin P2P Node on port {port} ===")
    
    # Initialize Xorcoin system
    system = XorcoinSystem()
    
    # Create P2P node
    node = P2PNode(system, host='127.0.0.1', port=port)
    
    # Start node
    node.start()
    
    # Connect to bootstrap peer if provided
    if bootstrap_peer:
        print(f"Connecting to bootstrap peer {bootstrap_peer[0]}:{bootstrap_peer[1]}")
        peer = node.connect_peer(bootstrap_peer[0], bootstrap_peer[1])
        if peer:
            print(f"Connected to {peer}")
        else:
            print("Failed to connect to bootstrap peer")
    
    # Run for a while
    try:
        while True:
            info = system.get_blockchain_info()
            peers = node.peer_manager.get_peer_count()
            
            print(f"\n[Port {port}] Status:")
            print(f"  Height: {info['height']}")
            print(f"  Peers: {peers}")
            print(f"  Mempool: {info['mempool_size']}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\nShutting down node on port {port}")
        node.stop()


def main():
    print("=== Xorcoin P2P Network Demo ===\n")
    
    # Start multiple nodes for testing
    if len(sys.argv) > 1:
        # Run single node
        port = int(sys.argv[1])
        bootstrap = None
        
        if len(sys.argv) > 3:
            bootstrap = (sys.argv[2], int(sys.argv[3]))
            
        run_node(port, bootstrap)
        
    else:
        print("Usage: python p2p_demo.py <port> [bootstrap_host bootstrap_port]")
        print("\nExample:")
        print("  Node 1: python p2p_demo.py 8333")
        print("  Node 2: python p2p_demo.py 8334 127.0.0.1 8333")


if __name__ == "__main__":
    main()
