"""
Enhanced Privacy System with Swarm Coordination - Simplified Version
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from ..swarms.mixing_coordinator import MixingEnhancedXorcoin
    SWARMS_AVAILABLE = True
except ImportError:
    SWARMS_AVAILABLE = False

class SwarmEnhancedPrivacySystem:
    def __init__(self, base_xorcoin_system):
        self.base_system = base_xorcoin_system
        
        if SWARMS_AVAILABLE:
            self.mixing_system = MixingEnhancedXorcoin(base_xorcoin_system)
            self.swarm_enabled = False
        else:
            self.mixing_system = base_xorcoin_system
            self.swarm_enabled = False
    
    def enable_swarm_coordination(self):
        if SWARMS_AVAILABLE and hasattr(self.mixing_system, 'start_mixing_coordinator'):
            self.mixing_system.start_mixing_coordinator()
            self.swarm_enabled = True
            logger.info("🔀 Swarm coordination enabled")
            return True
        return False
    
    def disable_swarm_coordination(self):
        if self.swarm_enabled and hasattr(self.mixing_system, 'stop_mixing_coordinator'):
            self.mixing_system.stop_mixing_coordinator()
            self.swarm_enabled = False
    
    def create_private_transaction(self, from_private_key, to_address: str, amount: int, 
                                 privacy_level: str = 'medium') -> Dict:
        # Get the from_address using your existing KeyManager
        try:
            from ..crypto.keys import KeyManager
            from_public_key = from_private_key.public_key()
            from_address = KeyManager.pubkey_to_address(from_public_key)
        except:
            # Fallback if KeyManager not available
            from_address = f"addr_{hash(str(from_private_key))}"[:40]
        
        result = {
            'privacy_level': privacy_level,
            'swarm_used': False,
            'transaction': None,
            'mixing_request_id': None,
            'status': 'created'
        }
        
        if privacy_level == 'high' and self.swarm_enabled and amount >= 1000:
            # Use swarm mixing for high privacy
            mix_id = self.mixing_system.request_coordinated_mixing(
                from_address=from_address,
                to_address=to_address,
                amount=amount
            )
            
            if mix_id:
                result.update({
                    'swarm_used': True,
                    'mixing_request_id': mix_id,
                    'status': 'mixing_requested'
                })
                logger.info(f"🔀 Swarm mixing requested: {mix_id}")
                return result
        
        # Fall back to regular transaction
        try:
            tx = self.mixing_system.create_transaction(
                from_address=from_address,
                to_address=to_address,
                amount=amount,
                private_key=from_private_key
            )
            
            if tx:
                
                success = self.mixing_system.add_transaction(tx)
                result.update({
                    'transaction': tx,
                    'status': 'completed' if success else 'failed'
                })
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def get_mixing_status(self, mixing_request_id: str) -> Dict:
        if self.swarm_enabled:
            return self.mixing_system.get_mixing_status(mixing_request_id)
        return {'status': 'swarm_not_available'}
    
    def get_privacy_report(self) -> Dict:
        report = {
            'swarm_enabled': self.swarm_enabled,
            'privacy_features': ['Basic transaction privacy', 'Enhanced privacy options'],
            'blockchain_info': self.mixing_system.get_blockchain_info()
        }
        
        if self.swarm_enabled:
            report['privacy_features'].append('Swarm-coordinated mixing')
            if hasattr(self.mixing_system, 'get_mixing_stats'):
                report['mixing_stats'] = self.mixing_system.get_mixing_stats()
        
        return report
    
    def __getattr__(self, name):
        return getattr(self.mixing_system, name)
