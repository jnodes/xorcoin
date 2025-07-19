"""
Simple Mixing Coordinator for Xorcoin - Complete Version
"""

import time
import secrets
import threading
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SimpleMixingCoordinator:
    def __init__(self):
        self.min_participants = 3
        self.max_participants = 8
        self.standard_amounts = [1000, 5000, 10000, 50000]
        self.pending_requests = defaultdict(list)
        self.active_rounds = {}
        self.completed_rounds = []
        self.coordinator_running = False
        self.coordination_thread = None
        
    def start_coordinator(self):
        if self.coordinator_running:
            return
        self.coordinator_running = True
        self.coordination_thread = threading.Thread(target=self._coordination_loop)
        self.coordination_thread.daemon = True
        self.coordination_thread.start()
        logger.info("🔀 Mixing coordinator started")
    
    def stop_coordinator(self):
        self.coordinator_running = False
        if self.coordination_thread:
            self.coordination_thread.join(timeout=5)
        logger.info("🛑 Mixing coordinator stopped")
    
    def request_mixing(self, amount: int, input_address: str, output_address: str) -> Optional[str]:
        standard_amount = self._get_standard_amount(amount)
        if not standard_amount:
            return None
        
        request_id = secrets.token_hex(8)
        request = {
            'request_id': request_id,
            'amount': standard_amount,
            'input_address': input_address,
            'output_address': output_address,
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        self.pending_requests[standard_amount].append(request)
        self._try_create_mixing_round(standard_amount)
        return request_id
    
    def get_mixing_status(self, request_id: str) -> Dict:
        # Search in pending requests
        for amount, requests in self.pending_requests.items():
            for request in requests:
                if request['request_id'] == request_id:
                    return {'status': request['status'], 'amount': request['amount']}
        
        # Search in active rounds
        for round_id, round_info in self.active_rounds.items():
            for request in round_info['requests']:
                if request['request_id'] == request_id:
                    return {'status': 'mixing', 'round_id': round_id}
        
        return {'status': 'not_found'}
    
    def _get_standard_amount(self, amount: int) -> Optional[int]:
        for std_amount in sorted(self.standard_amounts, reverse=True):
            if amount >= std_amount:
                return std_amount
        return None
    
    def _coordination_loop(self):
        while self.coordinator_running:
            try:
                for amount in self.standard_amounts:
                    self._try_create_mixing_round(amount)
                time.sleep(10)
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                time.sleep(30)
    
    def _try_create_mixing_round(self, amount: int):
        pending = self.pending_requests[amount]
        ready_requests = [r for r in pending if r['status'] == 'pending']
        
        if len(ready_requests) >= self.min_participants:
            selected_requests = ready_requests[:self.max_participants]
            self._create_mixing_round(amount, selected_requests)
    
    def _create_mixing_round(self, amount: int, requests: List[Dict]):
        round_id = secrets.token_hex(8)
        
        round_info = {
            'round_id': round_id,
            'amount': amount,
            'requests': requests,
            'participants': len(requests),
            'created_at': time.time(),
            'status': 'active'
        }
        
        for request in requests:
            request['status'] = 'mixing'
            request['round_id'] = round_id
            if request in self.pending_requests[amount]:
                self.pending_requests[amount].remove(request)
        
        self.active_rounds[round_id] = round_info
        logger.info(f"🔀 Created mixing round {round_id} with {len(requests)} participants")
    
    def get_coordinator_stats(self) -> Dict:
        total_pending = sum(len(requests) for requests in self.pending_requests.values())
        return {
            'running': self.coordinator_running,
            'pending_requests': total_pending,
            'active_rounds': len(self.active_rounds),
            'completed_rounds': len(self.completed_rounds)
        }

class MixingEnhancedXorcoin:
    def __init__(self, base_xorcoin_system):
        self.base_system = base_xorcoin_system
        self.mixing_coordinator = SimpleMixingCoordinator()
        
    def start_mixing_coordinator(self):
        self.mixing_coordinator.start_coordinator()
        
    def stop_mixing_coordinator(self):
        self.mixing_coordinator.stop_coordinator()
    
    def request_coordinated_mixing(self, from_address: str, to_address: str, amount: int) -> Optional[str]:
        return self.mixing_coordinator.request_mixing(amount, from_address, to_address)
    
    def get_mixing_status(self, request_id: str) -> Dict:
        return self.mixing_coordinator.get_mixing_status(request_id)
    
    def get_mixing_stats(self) -> Dict:
        return self.mixing_coordinator.get_coordinator_stats()
    
    def __getattr__(self, name):
        return getattr(self.base_system, name)
