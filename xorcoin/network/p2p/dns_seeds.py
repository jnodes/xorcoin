"""
DNS seed resolver for initial peer discovery
"""

import socket
import random
from typing import List, Tuple


class DNSSeedResolver:
    """Resolve DNS seeds to discover initial peers"""
    
    # DNS seeds for Xorcoin network
    DNS_SEEDS = [
        "seed1.xorcoin.org",
        "seed2.xorcoin.org", 
        "dnsseed.xorcoin.io",
        "seed.xorcoin.net"
    ]
    
    # Hardcoded bootstrap nodes as fallback
    BOOTSTRAP_NODES = [
        ("45.77.234.123", 8333),  # Example IPs - replace with real ones
        ("165.232.45.67", 8333),
        ("134.209.87.234", 8333),
        ("167.99.123.45", 8333)
    ]
    
    @staticmethod
    def get_peers_from_dns() -> List[Tuple[str, int]]:
        """Resolve DNS seeds to get peer addresses"""
        peers = []
        
        for seed in DNSSeedResolver.DNS_SEEDS:
            try:
                # Resolve DNS seed
                _, _, ips = socket.gethostbyname_ex(seed)
                # Add default port to each IP
                peers.extend([(ip, 8333) for ip in ips])
            except socket.gaierror:
                # DNS resolution failed, continue with next seed
                continue
            except Exception as e:
                print(f"Error resolving {seed}: {e}")
                
        # If no DNS seeds worked, use bootstrap nodes
        if not peers:
            peers = list(DNSSeedResolver.BOOTSTRAP_NODES)
            
        # Shuffle to distribute load
        random.shuffle(peers)
        
        return peers[:50]  # Return max 50 peers
        
    @staticmethod
    def add_custom_seed(host: str, port: int = 8333):
        """Add a custom bootstrap node"""
        DNSSeedResolver.BOOTSTRAP_NODES.append((host, port))
