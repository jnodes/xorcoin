"""
Network message types for Xorcoin P2P protocol
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Any
import json
import time


class MessageType(Enum):
    """P2P message types"""
    # Handshake
    VERSION = "version"
    VERACK = "verack"
    
    # Peer discovery
    GETADDR = "getaddr"
    ADDR = "addr"
    
    # Data synchronization
    GETBLOCKS = "getblocks"
    GETDATA = "getdata"
    BLOCK = "block"
    TX = "tx"
    
    # Inventory
    INV = "inv"
    NOTFOUND = "notfound"
    
    # Control
    PING = "ping"
    PONG = "pong"
    REJECT = "reject"
    
    # Mempool
    MEMPOOL = "mempool"
    GETMEMPOOL = "getmempool"


@dataclass
class Message:
    """Base message structure"""
    type: MessageType
    payload: dict
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def serialize(self) -> bytes:
        """Serialize message to bytes"""
        data = {
            'type': self.type.value,
            'payload': self.payload,
            'timestamp': self.timestamp
        }
        return json.dumps(data).encode()
    
    @staticmethod
    def deserialize(data: bytes) -> 'Message':
        """Deserialize message from bytes"""
        msg_data = json.loads(data.decode())
        return Message(
            type=MessageType(msg_data['type']),
            payload=msg_data['payload'],
            timestamp=msg_data.get('timestamp', time.time())
        )


@dataclass
class VersionMessage:
    """Version handshake message"""
    version: int = 1
    services: int = 1  # 1 = full node
    timestamp: int = None
    addr_recv: dict = None  # Receiving node's address
    addr_from: dict = None  # Sending node's address
    nonce: int = None
    user_agent: str = "Xorcoin:0.1.0"
    start_height: int = 0
    relay: bool = True
    
    def to_payload(self) -> dict:
        return {
            'version': self.version,
            'services': self.services,
            'timestamp': self.timestamp or int(time.time()),
            'addr_recv': self.addr_recv,
            'addr_from': self.addr_from,
            'nonce': self.nonce,
            'user_agent': self.user_agent,
            'start_height': self.start_height,
            'relay': self.relay
        }


@dataclass
class InvItem:
    """Inventory item"""
    type: str  # "block" or "tx"
    hash: str
    
    def to_dict(self) -> dict:
        return {'type': self.type, 'hash': self.hash}
    
    @staticmethod
    def from_dict(data: dict) -> 'InvItem':
        return InvItem(type=data['type'], hash=data['hash'])
