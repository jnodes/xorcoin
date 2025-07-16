"""
Peer representation and connection handling
"""

import socket
import threading
import time
from typing import Optional, Callable, List
from enum import Enum

from xorcoin.network.messages import Message, MessageType, NetworkProtocol


class PeerState(Enum):
    """Peer connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    HANDSHAKING = "handshaking"
    READY = "ready"
    DISCONNECTED = "disconnected"


class Peer:
    """Represents a network peer"""
    
    def __init__(self, host: str, port: int, inbound: bool = False):
        self.host = host
        self.port = port
        self.inbound = inbound
        self.socket: Optional[socket.socket] = None
        self.state = PeerState.DISCONNECTED
        
        # Peer info
        self.version: Optional[int] = None
        self.services: Optional[int] = None
        self.user_agent: Optional[str] = None
        self.start_height: Optional[int] = None
        
        # Connection stats
        self.connected_time: Optional[float] = None
        self.last_send: Optional[float] = None
        self.last_recv: Optional[float] = None
        self.bytes_sent = 0
        self.bytes_recv = 0
        
        # Callbacks
        self.on_message: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        
        # Threading
        self.receive_thread: Optional[threading.Thread] = None
        self.send_queue: List[bytes] = []
        self.send_lock = threading.Lock()
        self.running = False
        
    def connect(self) -> bool:
        """Connect to peer"""
        try:
            self.state = PeerState.CONNECTING
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # Remove timeout
            
            self.state = PeerState.CONNECTED
            self.connected_time = time.time()
            self.running = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.port} - {e}")
            self.state = PeerState.DISCONNECTED
            return False
    
    def accept_connection(self, sock: socket.socket):
        """Accept inbound connection"""
        self.socket = sock
        self.state = PeerState.CONNECTED
        self.connected_time = time.time()
        self.running = True
        
        # Get peer address
        try:
            self.host, self.port = sock.getpeername()
        except:
            pass
            
        # Start receive thread
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    def send_message(self, message: Message) -> bool:
        """Send message to peer"""
        try:
            # Serialize message
            payload = message.serialize()
            
            # Wrap with protocol
            data = NetworkProtocol.wrap_message(message.type.value, payload)
            
            # Send data
            with self.send_lock:
                self.socket.sendall(data)
                self.last_send = time.time()
                self.bytes_sent += len(data)
                
            return True
            
        except Exception as e:
            print(f"Error sending to {self.host}:{self.port} - {e}")
            self.disconnect()
            return False
    
    def _receive_loop(self):
        """Receive messages from peer"""
        buffer = b''
        
        while self.running:
            try:
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    break
                    
                buffer += data
                self.last_recv = time.time()
                self.bytes_recv += len(data)
                
                # Process complete messages
                while len(buffer) >= 24:  # Minimum header size
                    # Parse header
                    header_info = NetworkProtocol.parse_message_header(buffer[:24])
                    if not header_info:
                        # Invalid header, skip byte
                        buffer = buffer[1:]
                        continue
                        
                    command, length, checksum = header_info
                    
                    # Check if we have full message
                    if len(buffer) < 24 + length:
                        break
                        
                    # Extract payload
                    payload = buffer[24:24 + length]
                    buffer = buffer[24 + length:]
                    
                    # Verify checksum
                    if not NetworkProtocol.verify_checksum(payload, checksum):
                        print(f"Invalid checksum from {self.host}:{self.port}")
                        continue
                        
                    # Parse message
                    try:
                        message = Message.deserialize(payload)
                        if self.on_message:
                            self.on_message(self, message)
                    except Exception as e:
                        print(f"Error parsing message: {e}")
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receive error from {self.host}:{self.port} - {e}")
                break
                
        self.disconnect()
    
    def disconnect(self):
        """Disconnect from peer"""
        self.running = False
        self.state = PeerState.DISCONNECTED
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
                
        if self.on_disconnect:
            self.on_disconnect(self)
    
    def is_connected(self) -> bool:
        """Check if peer is connected"""
        return self.state in [PeerState.CONNECTED, PeerState.HANDSHAKING, PeerState.READY]
    
    def __str__(self):
        return f"Peer({self.host}:{self.port}, {self.state.value})"
