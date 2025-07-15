"""
Key management for Xorcoin
"""

import hashlib
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


class KeyManager:
    """Manages cryptographic keys for Xorcoin"""
    
    @staticmethod
    def generate_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey, str]:
        """
        Generate a new ECDSA keypair and address
        
        Returns:
            Tuple of (private_key, public_key, address)
        """
        private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        public_key = private_key.public_key()
        address = KeyManager.pubkey_to_address(public_key)
        return private_key, public_key, address
    
    @staticmethod
    def pubkey_to_address(public_key: ec.EllipticCurvePublicKey) -> str:
        """Convert public key to Xorcoin address (pubkey hash)"""
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        # SHA256 then RIPEMD160 (like Bitcoin)
        sha256_hash = hashlib.sha256(pub_bytes).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        return ripemd160.hexdigest()
    
    @staticmethod
    def serialize_private_key(private_key: ec.EllipticCurvePrivateKey, password: bytes) -> bytes:
        """Serialize and encrypt private key for storage"""
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password)
        )
    
    @staticmethod
    def serialize_public_key(public_key: ec.EllipticCurvePublicKey) -> bytes:
        """Serialize public key"""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    @staticmethod
    def load_private_key(key_bytes: bytes, password: bytes) -> ec.EllipticCurvePrivateKey:
        """Load private key from encrypted bytes"""
        return serialization.load_pem_private_key(
            key_bytes, 
            password=password, 
            backend=default_backend()
        )
    
    @staticmethod
    def load_public_key(key_bytes: bytes) -> ec.EllipticCurvePublicKey:
        """Load public key from bytes"""
        return serialization.load_pem_public_key(
            key_bytes,
            backend=default_backend()
        )
    
    @staticmethod
    def pubkey_bytes_to_hex(public_key: ec.EllipticCurvePublicKey) -> str:
        """Convert public key to hex string"""
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        return pub_bytes.hex()
