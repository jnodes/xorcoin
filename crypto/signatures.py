"""
Signature operations for Xorcoin
"""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.exceptions import InvalidSignature
from ecdsa import SECP256k1


class SignatureManager:
    """Handles signature creation and verification"""
    
    @staticmethod
    def normalize_signature(signature: bytes) -> bytes:
        """
        Enforce low S values for malleability prevention
        
        Args:
            signature: Raw signature bytes
            
        Returns:
            Normalized signature with low S value
        """
        # Decode DER signature
        r, s = utils.decode_dss_signature(signature)
        
        # Get curve order
        n = SECP256k1.order
        
        # Normalize S to low value
        if s > n // 2:
            s = n - s
            
        # Re-encode signature
        return utils.encode_dss_signature(r, s)
    
    @staticmethod
    def sign_message(private_key: ec.EllipticCurvePrivateKey, message: bytes) -> bytes:
        """
        Sign a message with private key
        
        Args:
            private_key: ECDSA private key
            message: Message to sign
            
        Returns:
            Normalized signature bytes
        """
        signature = private_key.sign(
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return SignatureManager.normalize_signature(signature)
    
    @staticmethod
    def verify_signature(
        public_key: ec.EllipticCurvePublicKey, 
        signature: bytes, 
        message: bytes
    ) -> bool:
        """
        Verify a signature
        
        Args:
            public_key: ECDSA public key
            signature: Signature to verify
            message: Original message
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Normalize signature before verification
            normalized_sig = SignatureManager.normalize_signature(signature)
            public_key.verify(
                normalized_sig,
                message,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    @staticmethod
    def sign_transaction_input(
        private_key: ec.EllipticCurvePrivateKey,
        tx_serialized: bytes
    ) -> bytes:
        """
        Sign a transaction input
        
        Args:
            private_key: Private key for signing
            tx_serialized: Serialized transaction data for this input
            
        Returns:
            Signature bytes
        """
        # Double SHA256 hash (like Bitcoin)
        hash1 = hashes.Hash(hashes.SHA256())
        hash1.update(tx_serialized)
        digest1 = hash1.finalize()
        
        hash2 = hashes.Hash(hashes.SHA256())
        hash2.update(digest1)
        message_hash = hash2.finalize()
        
        return SignatureManager.sign_message(private_key, message_hash)
