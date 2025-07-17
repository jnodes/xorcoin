"""
Peer scoring system for network behavior tracking
"""

import time
from typing import Dict
from enum import Enum


class PeerAction(Enum):
    """Peer actions that affect score"""
    # Positive actions
    VALID_BLOCK = 10
    VALID_TX = 2
    FAST_RESPONSE = 1
    
    # Negative actions
    INVALID_BLOCK = -50
    INVALID_TX = -20
    INVALID_MESSAGE = -10
    TIMEOUT = -5
    RATE_LIMIT = -20
    OVERSIZED_MESSAGE = -30
    PROTOCOL_VIOLATION = -40
    

class PeerScore:
    """Track peer behavior and reputation"""
    
    def __init__(self):
        self.score = 100  # Start with neutral score
        self.last_update = time.time()
        self.violation_count = 0
        self.total_messages = 0
        self.invalid_messages = 0
        
    def update(self, action: PeerAction) -> bool:
        """Update peer score based on action
        
        Returns:
            bool: True if peer should be banned
        """
        self.score += action.value
        self.last_update = time.time()
        
        if action.value < 0:
            self.violation_count += 1
            
        # Ban if score too low or too many violations
        if self.score <= 0 or self.violation_count >= 10:
            return True
            
        return False
        
    def get_reliability(self) -> float:
        """Calculate peer reliability percentage"""
        if self.total_messages == 0:
            return 100.0
            
        return ((self.total_messages - self.invalid_messages) / self.total_messages) * 100


class PeerScoreManager:
    """Manage scores for all peers"""
    
    def __init__(self):
        self.peer_scores: Dict[str, PeerScore] = {}
        
    def get_or_create_score(self, peer_id: str) -> PeerScore:
        """Get or create score for peer"""
        if peer_id not in self.peer_scores:
            self.peer_scores[peer_id] = PeerScore()
        return self.peer_scores[peer_id]
        
    def update_peer_score(self, peer_id: str, action: PeerAction) -> bool:
        """Update peer score and check if should ban"""
        score = self.get_or_create_score(peer_id)
        return score.update(action)
        
    def get_peer_reputation(self, peer_id: str) -> int:
        """Get current reputation score"""
        score = self.peer_scores.get(peer_id)
        return score.score if score else 100
