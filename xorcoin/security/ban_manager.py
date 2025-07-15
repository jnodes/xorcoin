"""
Peer ban management
"""
import time
from typing import Dict, Set

class BanManager:
    def __init__(self):
        self.ban_scores: Dict[str, int] = {}
        self.banned_peers: Dict[str, float] = {}
        self.BAN_THRESHOLD = 100
        self.BAN_DURATION = 86400  # 24 hours
        
    def increase_ban_score(self, peer_ip: str, score: int, reason: str):
        """Increase ban score for misbehaving peer"""
        current_score = self.ban_scores.get(peer_ip, 0)
        new_score = current_score + score
        self.ban_scores[peer_ip] = new_score
        
        if new_score >= self.BAN_THRESHOLD:
            self.ban_peer(peer_ip, reason)
            
    def ban_peer(self, peer_ip: str, reason: str):
        """Ban a peer"""
        self.banned_peers[peer_ip] = time.time() + self.BAN_DURATION
        self.ban_scores.pop(peer_ip, None)
        print(f"Banned peer {peer_ip}: {reason}")
        
    def is_banned(self, peer_ip: str) -> bool:
        """Check if peer is banned"""
        if peer_ip in self.banned_peers:
            if time.time() < self.banned_peers[peer_ip]:
                return True
            else:
                # Ban expired
                del self.banned_peers[peer_ip]
        return False
