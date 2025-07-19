"""
Xorcoin Privacy Package
Enhanced privacy features with optional swarm coordination
"""

try:
    from .swarm_privacy import SwarmEnhancedPrivacySystem
    __all__ = ['SwarmEnhancedPrivacySystem']
except ImportError:
    # Fallback if swarms not available
    __all__ = []
