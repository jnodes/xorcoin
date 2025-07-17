"""
Improved P2P node implementation with security and proper sync
"""

import socket
import threading
import time
import random
from typing import Optional, List, Dict, Set

from xorcoin.network.p2p.peer import Peer, PeerState
from xorcoin.network.p2p.peer_manager import PeerManager
from xorcoin.network.p2p.scoring import PeerScoreManager, PeerAction
from xorcoin.network.p2p.dns_seeds import DNSSeedResolver
from xorcoin.network.messages import Message, MessageType, VersionMessage, InvItem
from xorcoin.network.messages.serialization import NetworkSerializer
from xorcoin.security.rate_limiter import RateLimiter, MessageSizeLimiter
from xorcoin.core.models import Block, Transaction


class ImprovedP2PNode:
    """Enhanced P2P network node with security features"""
    
    def __init__(self, xorcoin_system, host: str = '0.0.0.0', port: int = 8333):
        self.system = xorcoin_system
        self.host = host
        self.port = port
        
        # Network components
        self.peer_manager = PeerManager()
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
        # Security components
        self.connection_limits = {
            'max_connections_per_ip': 3,
            'max_inbound_connections': 100,
            'max_outbound_connections': 8
        }
        self.peer_score_manager = PeerScoreManager()
        self.message_rate_limiter = RateLimiter(max_messages_per_minute=120)
        
        # Node identification
        self.node_id = random.randint(1, 2**64)
        
        # Sync state
        self.syncing = False
        self.sync_peer: Optional[Peer] = None
        self.sync_start_height = 0
        
        # Message handlers
        self.message_handlers = {
            MessageType.VERSION: self._handle_version,
            MessageType.VERACK: self._handle_verack,
            MessageType.PING: self._handle_ping,
            MessageType.PONG: self._handle_pong,
            MessageType.GETADDR: self._handle_getaddr,
            MessageType.ADDR: self._handle_addr,
            MessageType.INV: self._handle_inv,
            MessageType.GETDATA: self._handle_getdata,
            MessageType.BLOCK: self._handle_block,
            MessageType.TX: self._handle_tx,
            MessageType.GETBLOCKS: self._handle_getblocks,
        }
        
        # Inventory tracking
        self.requested_blocks: Set[str] = set()
        self.requested_txs: Set[str] = set()
        
        # Connection tracking
        self.connections_per_ip: Dict[str, int] = {}
        
    def start(self):
        """Start P2P node with initial peer discovery"""
        self.running = True
        
        # Start server
        self._start_server()
        
        # Discover initial peers
        self._discover_initial_peers()
        
        # Start maintenance thread
        maintenance_thread = threading.Thread(target=self._maintenance_loop)
        maintenance_thread.daemon = True
        maintenance_thread.start()
        
        print(f"P2P node started on {self.host}:{self.port}")
        
    def _discover_initial_peers(self):
        """Discover initial peers from DNS seeds"""
        print("Discovering initial peers...")
        
        # Get peers from DNS seeds
        seed_peers = DNSSeedResolver.get_peers_from_dns()
        
        # Try to connect to some peers
        for host, port in seed_peers[:10]:  # Try first 10
            if self.peer_manager.get_peer_count() >= 8:
                break
            self.connect_peer(host, port)
            
    def _start_server(self):
        """Start listening for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        
        accept_thread = threading.Thread(target=self._accept_loop)
        accept_thread.daemon = True
        accept_thread.start()
        
    def _accept_loop(self):
        """Accept incoming peer connections with security checks"""
        while self.running:
            try:
                sock, addr = self.server_socket.accept()
                
                # Check connection limits
                if not self._enforce_connection_limits(addr[0]):
                    sock.close()
                    continue
                    
                # Check if banned
                if self.system.ban_manager.is_banned(addr[0]):
                    sock.close()
                    continue
                    
                # Check total peer limit
                if self.peer_manager.get_peer_count() >= self.peer_manager.max_peers:
                    sock.close()
                    continue
                    
                # Create inbound peer
                peer = Peer(addr[0], addr[1], inbound=True)
                peer.accept_connection(sock)
                peer.on_message = self._handle_peer_message
                peer.on_disconnect = self._handle_peer_disconnect
                
                # Add to peer manager
                peer_id = f"{addr[0]}:{addr[1]}"
                with self.peer_manager.peer_lock:
                    self.peer_manager.peers[peer_id] = peer
                    
                # Track connection
                self.connections_per_ip[addr[0]] = self.connections_per_ip.get(addr[0], 0) + 1
                    
                print(f"Accepted connection from {addr[0]}:{addr[1]}")
                
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")
                    
    def _enforce_connection_limits(self, peer_ip: str) -> bool:
        """Check if connection should be allowed"""
        # Check connections from this IP
        current_connections = self.connections_per_ip.get(peer_ip, 0)
        if current_connections >= self.connection_limits['max_connections_per_ip']:
            return False
            
        # Check total inbound connections
        inbound_count = sum(
            1 for p in self.peer_manager.peers.values()
            if p.inbound
        )
        
        if inbound_count >= self.connection_limits['max_inbound_connections']:
            return False
            
        return True
        
    def _handle_peer_disconnect(self, peer: Peer):
        """Handle peer disconnection"""
        # Update connection tracking
        if peer.host in self.connections_per_ip:
            self.connections_per_ip[peer.host] -= 1
            if self.connections_per_ip[peer.host] <= 0:
                del self.connections_per_ip[peer.host]
                
        # Remove from peer manager
        self.peer_manager.remove_peer(peer)
        
    def _handle_peer_message(self, peer: Peer, message: Message):
        """Handle incoming peer message with validation"""
        peer_id = f"{peer.host}:{peer.port}"
        
        # Validate message
        if not self._validate_message(peer, message):
            return
            
        # Update peer statistics
        score = self.peer_score_manager.get_or_create_score(peer_id)
        score.total_messages += 1
        
        # Handle message
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                handler(peer, message)
            except Exception as e:
                print(f"Error handling {message.type} from {peer}: {e}")
                score.invalid_messages += 1
                
                # Update peer score
                if self.peer_score_manager.update_peer_score(peer_id, PeerAction.INVALID_MESSAGE):
                    self._ban_peer(peer)
        else:
            print(f"Unknown message type: {message.type}")
            
    def _validate_message(self, peer: Peer, message: Message) -> bool:
        """Validate incoming message"""
        peer_id = f"{peer.host}:{peer.port}"
        
        # Check message size
        if len(message.serialize()) > MessageSizeLimiter.MAX_MESSAGE_SIZE:
            if self.peer_score_manager.update_peer_score(peer_id, PeerAction.OVERSIZED_MESSAGE):
                self._ban_peer(peer)
            return False
            
        # Check rate limiting
        if not self.message_rate_limiter.is_allowed(peer.host):
            if self.peer_score_manager.update_peer_score(peer_id, PeerAction.RATE_LIMIT):
                self._ban_peer(peer)
            return False
            
        # Validate specific message types
        if message.type == MessageType.INV:
            items = message.payload.get('items', [])
            if len(items) > MessageSizeLimiter.MAX_INV_ITEMS:
                if self.peer_score_manager.update_peer_score(peer_id, PeerAction.PROTOCOL_VIOLATION):
                    self._ban_peer(peer)
                return False
                
        return True
        
    def _ban_peer(self, peer: Peer):
        """Ban a misbehaving peer"""
        self.system.ban_manager.ban_peer(peer.host, "Poor behavior score")
        peer.disconnect()
        
    # Implement proper getblocks handler
    def _handle_getblocks(self, peer: Peer, message: Message):
        """Handle getblocks message"""
        locator = message.payload.get('locator', [])
        stop_hash = message.payload.get('stop_hash', '00' * 32)
        
        # Find common ancestor
        start_height = 0
        for block_hash in locator:
            for i, block in enumerate(self.system.blockchain.chain):
                if block.get_header_hash() == block_hash:
                    start_height = i + 1
                    break
                    
        # Send inventory of blocks
        inv_items = []
        for i in range(start_height, min(start_height + 500, len(self.system.blockchain.chain))):
            block = self.system.blockchain.chain[i]
            inv_items.append(InvItem('block', block.get_header_hash()).to_dict())
            
            if block.get_header_hash() == stop_hash:
                break
                
        if inv_items:
            peer.send_message(Message(MessageType.INV, {'items': inv_items}))
            
    # Update block handler with proper serialization
    def _handle_block(self, peer: Peer, message: Message):
        """Handle block message"""
        peer_id = f"{peer.host}:{peer.port}"
        block_data = message.payload.get('block')
        if not block_data:
            return
            
        # Deserialize block
        block = NetworkSerializer.deserialize_block(block_data)
        if not block:
            # Invalid block
            if self.peer_score_manager.update_peer_score(peer_id, PeerAction.INVALID_BLOCK):
                self._ban_peer(peer)
            return
            
        # Remove from requested
        block_hash = block.get_header_hash()
        self.requested_blocks.discard(block_hash)
        
        # Process block
        # TODO: Add to blockchain with proper validation
        print(f"Received block {block.height} from {peer}")
        
        # Reward peer for valid block
        self.peer_score_manager.update_peer_score(peer_id, PeerAction.VALID_BLOCK)
        
    # Update transaction handler  
    def _handle_tx(self, peer: Peer, message: Message):
        """Handle transaction message"""
        peer_id = f"{peer.host}:{peer.port}"
        tx_data = message.payload.get('tx')
        if not tx_data:
            return
            
        # Deserialize transaction
        tx = NetworkSerializer.deserialize_transaction(tx_data)
        if not tx:
            # Invalid transaction
            if self.peer_score_manager.update_peer_score(peer_id, PeerAction.INVALID_TX):
                self._ban_peer(peer)
            return
            
        # Remove from requested
        tx_hash = tx.get_hash()
        self.requested_txs.discard(tx_hash)
        
        # Add to mempool
        if self.system.add_transaction(tx):
            # Relay to other peers
            inv_msg = Message(MessageType.INV, {
                'items': [InvItem('tx', tx_hash).to_dict()]
            })
            self.peer_manager.broadcast_message(inv_msg, exclude_peer=peer)
            
            # Reward peer
            self.peer_score_manager.update_peer_score(peer_id, PeerAction.VALID_TX)
            
    # Implement proper sync checking
    def _check_sync_needed(self):
        """Check if blockchain sync is needed"""
        if self.syncing:
            return
            
        # Get best height from peers
        best_height = 0
        best_peer = None
        
        for peer in self.peer_manager.get_connected_peers():
            if peer.start_height and peer.start_height > best_height:
                best_height = peer.start_height
                best_peer = peer
                
        our_height = len(self.system.blockchain.chain)
        
        # Start sync if we're behind
        if best_height > our_height + 1:
            self.syncing = True
            self.sync_peer = best_peer
            self.sync_start_height = our_height
            self._start_sync()
            
    def _start_sync(self):
        """Start blockchain synchronization"""
        if not self.sync_peer:
            return
            
        print(f"Starting sync from height {self.sync_start_height}")
        
        # Build block locator
        locator = self._build_block_locator()
        
        # Send getblocks
        self.sync_peer.send_message(Message(MessageType.GETBLOCKS, {
            'locator': locator,
            'stop_hash': '00' * 32
        }))
        
    def _build_block_locator(self) -> List[str]:
        """Build block locator for sync"""
        locator = []
        chain = self.system.blockchain.chain
        
        # Add recent blocks
        step = 1
        index = len(chain) - 1
        
        while index > 0:
            locator.append(chain[index].get_header_hash())
            index -= step
            
            # Exponentially increase step
            if len(locator) > 10:
                step *= 2
                
        # Always add genesis
        locator.append(chain[0].get_header_hash())
        
        return locator
        
    # Update serialization methods
    def _serialize_block(self, block: Block) -> dict:
        """Serialize block for network transmission"""
        return NetworkSerializer.serialize_block(block)
        
    def _deserialize_block(self, data: dict) -> Optional[Block]:
        """Deserialize block from network data"""
        return NetworkSerializer.deserialize_block(data)
        
    def _serialize_transaction(self, tx: Transaction) -> dict:
        """Serialize transaction for network transmission"""
        return NetworkSerializer.serialize_transaction(tx)
        
    def _deserialize_transaction(self, data: dict) -> Optional[Transaction]:
        """Deserialize transaction from network data"""
        return NetworkSerializer.deserialize_transaction(data)
