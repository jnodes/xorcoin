"""
Manages peer connections and discovery
"""

import threading
import time
import random
from typing import List, Dict, Optional, Set

from xorcoin.network.p2p.peer import Peer, PeerState
from xorcoin.network.messages import Message, MessageType


class PeerManager:
    """Manages P2P peer connections"""
    
    def __init__(self, max_peers: int = 8):
        self.max_peers = max_peers
        self.peers: Dict[str, Peer] = {}
        self.peer_lock = threading.Lock()
        
        # Known peer addresses
        self.known_peers: Set[tuple] = set()
        
        # Bootstrap nodes
        self.bootstrap_nodes = [
            # Add your bootstrap nodes here
            # ("seed1.xorcoin.com", 8333),
            # ("seed2.xorcoin.com", 8333),
        ]
        
        # Ban list
        self.banned_peers: Dict[str, float] = {}
        
    def add_peer(self, host: str, port: int) -> Optional[Peer]:
        """Add and connect to a new peer"""
        peer_id = f"{host}:{port}"
        
        # Check if already connected
        with self.peer_lock:
            if peer_id in self.peers:
                return self.peers[peer_id]
                
            # Check if banned
            if host in self.banned_peers:
                if time.time() < self.banned_peers[host]:
                    return None
                else:
                    del self.banned_peers[host]
                    
            # Check peer limit
            if len(self.peers) >= self.max_peers:
                return None
                
        # Create and connect peer
        peer = Peer(host, port)
        if peer.connect():
            with self.peer_lock:
                self.peers[peer_id] = peer
                self.known_peers.add((host, port))
            return peer
        
        return None
    
    def remove_peer(self, peer: Peer):
        """Remove a peer"""
        peer_id = f"{peer.host}:{peer.port}"
        with self.peer_lock:
            if peer_id in self.peers:
                del self.peers[peer_id]
                
    def get_connected_peers(self) -> List[Peer]:
        """Get list of connected peers"""
        with self.peer_lock:
            return [p for p in self.peers.values() if p.is_connected()]
            
    def broadcast_message(self, message: Message, exclude_peer: Optional[Peer] = None):
        """Broadcast message to all connected peers"""
        peers = self.get_connected_peers()
        for peer in peers:
            if peer != exclude_peer and peer.state == PeerState.READY:
                peer.send_message(message)
                
    def discover_peers(self):
        """Discover new peers from existing connections"""
        # Send getaddr to random peers
        peers = self.get_connected_peers()
        if peers:
            selected = random.sample(peers, min(3, len(peers)))
            for peer in selected:
                peer.send_message(Message(MessageType.GETADDR, {}))
                
    def ban_peer(self, host: str, duration: int = 86400):
        """Ban a peer for specified duration (default 24 hours)"""
        self.banned_peers[host] = time.time() + duration
        
        # Disconnect if connected
        with self.peer_lock:
            for peer_id, peer in list(self.peers.items()):
                if peer.host == host:
                    peer.disconnect()
                    del self.peers[peer_id]
                    
    def get_peer_count(self) -> int:
        """Get number of connected peers"""
        return len(self.get_connected_peers())
    
    def maintain_connections(self):
        """Maintain target number of peer connections"""
        current_count = self.get_peer_count()
        
        if current_count < self.max_peers:
            # Try to connect to more peers
            needed = self.max_peers - current_count
            
            # First try known peers
            available_peers = list(self.known_peers)
            random.shuffle(available_peers)
            
            for host, port in available_peers[:needed]:
                peer_id = f"{host}:{port}"
                if peer_id not in self.peers:
                    self.add_peer(host, port)
                    
            # If still need more, try bootstrap nodes
            if self.get_peer_count() < self.max_peers // 2:
                for host, port in self.bootstrap_nodes:
                    peer_id = f"{host}:{port}"
                    if peer_id not in self.peers:
                        self.add_peer(host, port)
