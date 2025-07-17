"""
Network monitoring and statistics
"""

import time
import threading
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class NetworkStats:
    """Network statistics"""
    start_time: float = field(default_factory=time.time)
    
    # Connection stats
    total_connections: int = 0
    current_connections: int = 0
    failed_connections: int = 0
    
    # Message stats
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    
    # Block/TX stats
    blocks_received: int = 0
    txs_received: int = 0
    
    # Peer stats
    banned_peers: int = 0
    
    def get_uptime(self) -> float:
        """Get network uptime in seconds"""
        return time.time() - self.start_time
        
    def get_message_rate(self) -> float:
        """Get messages per second"""
        uptime = self.get_uptime()
        if uptime == 0:
            return 0
        return self.messages_received / uptime
        
    def get_bandwidth_usage(self) -> Dict[str, float]:
        """Get bandwidth usage in KB/s"""
        uptime = self.get_uptime()
        if uptime == 0:
            return {"download": 0, "upload": 0}
            
        return {
            "download": (self.bytes_received / 1024) / uptime,
            "upload": (self.bytes_sent / 1024) / uptime
        }


class NetworkMonitor:
    """Monitor network health and statistics"""
    
    def __init__(self, node):
        self.node = node
        self.stats = NetworkStats()
        self.peer_latencies: Dict[str, List[float]] = {}
        self.monitoring = False
        
    def start(self):
        """Start monitoring"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            # Update current connections
            self.stats.current_connections = self.node.peer_manager.get_peer_count()
            
            # Print periodic status
            if int(time.time()) % 60 == 0:  # Every minute
                self._print_status()
                
            time.sleep(1)
            
    def _print_status(self):
        """Print network status"""
        print("\n=== Network Status ===")
        print(f"Uptime: {self.stats.get_uptime()/3600:.2f} hours")
        print(f"Peers: {self.stats.current_connections}")
        print(f"Messages: {self.stats.messages_received} received, {self.stats.messages_sent} sent")
        print(f"Message rate: {self.stats.get_message_rate():.2f} msg/s")
        
        bandwidth = self.stats.get_bandwidth_usage()
        print(f"Bandwidth: ↓ {bandwidth['download']:.2f} KB/s, ↑ {bandwidth['upload']:.2f} KB/s")
        
        print(f"Blocks received: {self.stats.blocks_received}")
        print(f"Transactions received: {self.stats.txs_received}")
        print(f"Banned peers: {self.stats.banned_peers}")
        print("====================\n")
        
    def record_message(self, sent: bool, size: int):
        """Record message statistics"""
        if sent:
            self.stats.messages_sent += 1
            self.stats.bytes_sent += size
        else:
            self.stats.messages_received += 1
            self.stats.bytes_received += size
            
    def record_peer_latency(self, peer_id: str, latency: float):
        """Record peer latency"""
        if peer_id not in self.peer_latencies:
            self.peer_latencies[peer_id] = []
            
        self.peer_latencies[peer_id].append(latency)
        
        # Keep only last 100 measurements
        if len(self.peer_latencies[peer_id]) > 100:
            self.peer_latencies[peer_id] = self.peer_latencies[peer_id][-100:]
