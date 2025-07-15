"""
Rate limiting for network connections
"""
import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request from IP is allowed"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
            
        self.requests[client_ip].append(current_time)
        return True
        
class MessageSizeLimiter:
    MAX_MESSAGE_SIZE = 32 * 1024 * 1024  # 32MB
    MAX_INV_ITEMS = 50000
    
    @staticmethod
    def validate_message_size(data: bytes) -> bool:
        return len(data) <= MessageSizeLimiter.MAX_MESSAGE_SIZE
