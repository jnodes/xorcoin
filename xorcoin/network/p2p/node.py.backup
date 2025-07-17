"""
Main P2P node implementation
"""

import socket
from typing import Optional, List, Dict, Set
import threading
import time
import random
from typing import Optional, List, Dict

from xorcoin.network.p2p.peer import Peer, PeerState
from xorcoin.network.p2p.peer_manager import PeerManager
from xorcoin.network.messages import Message, MessageType, VersionMessage, InvItem
from xorcoin.core.models import Block, Transaction


class P2PNode:
    """Main P2P network node"""
    
    def __init__(self, xorcoin_system, host: str = '0.0.0.0', port: int = 8333):
        self.system = xorcoin_system
        self.host = host
        self.port = port
        
        # Network components
        self.peer_manager = PeerManager()
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
        # Node identification
        self.node_id = random.randint(1, 2**64)
        
        # Sync state
        self.syncing = False
        self.sync_peer: Optional[Peer] = None
        
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
        
    def start(self):
        """Start P2P node"""
        self.running = True
        
        # Start server
        self._start_server()
        
        # Start maintenance thread
        maintenance_thread = threading.Thread(target=self._maintenance_loop)
        maintenance_thread.daemon = True
        maintenance_thread.start()
        
        print(f"P2P node started on {self.host}:{self.port}")
        
    def stop(self):
        """Stop P2P node"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
            
        # Disconnect all peers
        for peer in list(self.peer_manager.peers.values()):
            peer.disconnect()
            
    def _start_server(self):
        """Start listening for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        
        # Accept connections in separate thread
        accept_thread = threading.Thread(target=self._accept_loop)
        accept_thread.daemon = True
        accept_thread.start()
        
    def _accept_loop(self):
        """Accept incoming peer connections"""
        while self.running:
            try:
                sock, addr = self.server_socket.accept()
                
                # Check peer limit
                if self.peer_manager.get_peer_count() >= self.peer_manager.max_peers:
                    sock.close()
                    continue
                    
                # Create inbound peer
                peer = Peer(addr[0], addr[1], inbound=True)
                peer.accept_connection(sock)
                peer.on_message = self._handle_peer_message
                peer.on_disconnect = self.peer_manager.remove_peer
                
                # Add to peer manager
                peer_id = f"{addr[0]}:{addr[1]}"
                with self.peer_manager.peer_lock:
                    self.peer_manager.peers[peer_id] = peer
                    
                print(f"Accepted connection from {addr[0]}:{addr[1]}")
                
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")
                    
    def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.running:
            try:
                # Maintain peer connections
                self.peer_manager.maintain_connections()
                
                # Discover new peers
                if random.random() < 0.1:  # 10% chance
                    self.peer_manager.discover_peers()
                    
                # Sync blockchain if needed
                if not self.syncing:
                    self._check_sync_needed()
                    
                # Broadcast new blocks/transactions
                self._broadcast_inventory()
                
            except Exception as e:
                print(f"Maintenance error: {e}")
                
            time.sleep(30)  # Run every 30 seconds
            
    def connect_peer(self, host: str, port: int) -> Optional[Peer]:
        """Connect to a specific peer"""
        peer = self.peer_manager.add_peer(host, port)
        if peer:
            peer.on_message = self._handle_peer_message
            peer.on_disconnect = self.peer_manager.remove_peer
            
            # Send version handshake
            self._send_version(peer)
            
        return peer
        
    def _handle_peer_message(self, peer: Peer, message: Message):
        """Handle incoming peer message"""
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                handler(peer, message)
            except Exception as e:
                print(f"Error handling {message.type} from {peer}: {e}")
        else:
            print(f"Unknown message type: {message.type}")
            
    def _send_version(self, peer: Peer):
        """Send version message to peer"""
        version_msg = VersionMessage(
            version=1,
            services=1,
            timestamp=int(time.time()),
            addr_recv={'host': peer.host, 'port': peer.port},
            addr_from={'host': self.host, 'port': self.port},
            nonce=self.node_id,
            user_agent="Xorcoin:0.1.0",
            start_height=len(self.system.blockchain.chain),
            relay=True
        )
        
        peer.send_message(Message(MessageType.VERSION, version_msg.to_payload()))
        peer.state = PeerState.HANDSHAKING
        
    def _handle_version(self, peer: Peer, message: Message):
        """Handle version message"""
        payload = message.payload
        
        # Store peer info
        peer.version = payload['version']
        peer.services = payload['services']
        peer.user_agent = payload['user_agent']
        peer.start_height = payload['start_height']
        
        # Send verack
        peer.send_message(Message(MessageType.VERACK, {}))
        
        # Send version if not sent yet
        if peer.state == PeerState.CONNECTED:
            self._send_version(peer)
            
    def _handle_verack(self, peer: Peer, message: Message):
        """Handle verack message"""
        peer.state = PeerState.READY
        print(f"Handshake complete with {peer}")
        
        # Request peer addresses
        peer.send_message(Message(MessageType.GETADDR, {}))
        
    def _handle_ping(self, peer: Peer, message: Message):
        """Handle ping message"""
        # Respond with pong
        peer.send_message(Message(MessageType.PONG, message.payload))
        
    def _handle_pong(self, peer: Peer, message: Message):
        """Handle pong message"""
        # Update last received time
        peer.last_recv = time.time()
        
    def _handle_getaddr(self, peer: Peer, message: Message):
        """Handle getaddr message"""
        # Send known peer addresses
        known_addrs = []
        for (host, port) in list(self.peer_manager.known_peers)[:100]:
            known_addrs.append({
                'timestamp': int(time.time()),
                'services': 1,
                'host': host,
                'port': port
            })
            
        if known_addrs:
            peer.send_message(Message(MessageType.ADDR, {'addrs': known_addrs}))
            
    def _handle_addr(self, peer: Peer, message: Message):
        """Handle addr message"""
        addrs = message.payload.get('addrs', [])
        
        for addr in addrs[:1000]:  # Limit to prevent spam
            host = addr.get('host')
            port = addr.get('port', 8333)
            
            if host and port:
                self.peer_manager.known_peers.add((host, port))
                
    def _handle_inv(self, peer: Peer, message: Message):
        """Handle inventory message"""
        items = message.payload.get('items', [])
        
        # Request unknown items
        to_request = []
        for item_data in items:
            inv_item = InvItem.from_dict(item_data)
            
            if inv_item.type == 'block':
                # Check if we have this block
                if not self._have_block(inv_item.hash):
                    to_request.append(inv_item)
                    self.requested_blocks.add(inv_item.hash)
                    
            elif inv_item.type == 'tx':
                # Check if we have this transaction
                if not self._have_transaction(inv_item.hash):
                    to_request.append(inv_item)
                    self.requested_txs.add(inv_item.hash)
                    
        if to_request:
            peer.send_message(Message(MessageType.GETDATA, {
                'items': [item.to_dict() for item in to_request]
            }))
            
    def _handle_getdata(self, peer: Peer, message: Message):
        """Handle getdata message"""
        items = message.payload.get('items', [])
        
        for item_data in items:
            inv_item = InvItem.from_dict(item_data)
            
            if inv_item.type == 'block':
                block = self._get_block(inv_item.hash)
                if block:
                    peer.send_message(Message(MessageType.BLOCK, {
                        'block': self._serialize_block(block)
                    }))
                    
            elif inv_item.type == 'tx':
                tx = self._get_transaction(inv_item.hash)
                if tx:
                    peer.send_message(Message(MessageType.TX, {
                        'tx': self._serialize_transaction(tx)
                    }))
                    
    def _handle_block(self, peer: Peer, message: Message):
        """Handle block message"""
        block_data = message.payload.get('block')
        if not block_data:
            return
            
        # Deserialize block
        block = self._deserialize_block(block_data)
        if not block:
            return
            
        # Remove from requested
        block_hash = block.get_header_hash()
        self.requested_blocks.discard(block_hash)
        
        # Process block
        # TODO: Add to blockchain
        print(f"Received block {block.height} from {peer}")
        
    def _handle_tx(self, peer: Peer, message: Message):
        """Handle transaction message"""
        tx_data = message.payload.get('tx')
        if not tx_data:
            return
            
        # Deserialize transaction
        tx = self._deserialize_transaction(tx_data)
        if not tx:
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
            
    def _handle_getblocks(self, peer: Peer, message: Message):
        """Handle getblocks message"""
        # TODO: Implement block locator logic
        pass
        
    def _check_sync_needed(self):
        """Check if blockchain sync is needed"""
        # TODO: Implement sync logic
        pass
        
    def _broadcast_inventory(self):
        """Broadcast new blocks and transactions"""
        # TODO: Implement inventory broadcast
        pass
        
    # Helper methods
    def _have_block(self, block_hash: str) -> bool:
        """Check if we have a block"""
        for block in self.system.blockchain.chain:
            if block.get_header_hash() == block_hash:
                return True
        return False
        
    def _have_transaction(self, tx_hash: str) -> bool:
        """Check if we have a transaction"""
        return tx_hash in self.system.mempool.transactions or \
               tx_hash in self.system.confirmed_txs
               
    def _get_block(self, block_hash: str) -> Optional[Block]:
        """Get block by hash"""
        for block in self.system.blockchain.chain:
            if block.get_header_hash() == block_hash:
                return block
        return None
        
    def _get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """Get transaction by hash"""
        if tx_hash in self.system.mempool.transactions:
            return self.system.mempool.transactions[tx_hash]
        if tx_hash in self.system.confirmed_txs:
            return self.system.confirmed_txs[tx_hash]
        return None
        
    def _serialize_block(self, block: Block) -> dict:
        """Serialize block for network transmission"""
        # TODO: Implement proper serialization
        return {}
        
    def _deserialize_block(self, data: dict) -> Optional[Block]:
        """Deserialize block from network data"""
        # TODO: Implement proper deserialization
        return None
        
    def _serialize_transaction(self, tx: Transaction) -> dict:
        """Serialize transaction for network transmission"""
        # TODO: Implement proper serialization
        return {}
        
    def _deserialize_transaction(self, data: dict) -> Optional[Transaction]:
        """Deserialize transaction from network data"""
        # TODO: Implement proper deserialization
        return None
