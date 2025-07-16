"""
Network protocol implementation
"""

import hashlib
import struct
from typing import Optional, Tuple

class NetworkProtocol:
    """Handles network protocol encoding/decoding"""
    
    # Network magic bytes (identifies Xorcoin network)
    MAGIC_BYTES = b'\xf9\xbe\xb4\xd9'  # Can be customized
    PROTOCOL_VERSION = 1
    
    @staticmethod
    def create_message_header(command: str, payload: bytes) -> bytes:
        """Create message header with checksum"""
        # Command (12 bytes, null-padded)
        command_bytes = command.encode('ascii')[:12].ljust(12, b'\x00')
        
        # Payload length (4 bytes, little-endian)
        length = struct.pack('<I', len(payload))
        
        # Checksum (first 4 bytes of double SHA256)
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        
        return NetworkProtocol.MAGIC_BYTES + command_bytes + length + checksum
    
    @staticmethod
    def wrap_message(command: str, payload: bytes) -> bytes:
        """Wrap payload with protocol header"""
        header = NetworkProtocol.create_message_header(command, payload)
        return header + payload
    
    @staticmethod
    def parse_message_header(data: bytes) -> Optional[Tuple[str, int, bytes]]:
        """Parse message header, returns (command, payload_length, checksum)"""
        if len(data) < 24:
            return None
            
        # Check magic bytes
        if data[:4] != NetworkProtocol.MAGIC_BYTES:
            return None
            
        # Extract fields
        command = data[4:16].rstrip(b'\x00').decode('ascii')
        length = struct.unpack('<I', data[16:20])[0]
        checksum = data[20:24]
        
        return (command, length, checksum)
    
    @staticmethod
    def verify_checksum(payload: bytes, expected_checksum: bytes) -> bool:
        """Verify payload checksum"""
        actual = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return actual == expected_checksum
