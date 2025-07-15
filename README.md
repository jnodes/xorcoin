Xorcoin

A minimalistic secure UTXO-based token system with blockchain implementation, improving on Bitcoin's core concepts.

Features

- UTXO Model: Efficient transaction tracking with Unspent Transaction Outputs
- ECDSA Cryptography: Secure key generation and transaction signing using SECP256K1
- Blockchain: Full blockchain implementation with proof-of-work mining
- Security Features:
  - Replay protection with chain IDs
  - Transaction malleability prevention
  - Double-spend protection
  - Secure key storage with encryption
  - TLS networking support
- Transaction Validation: Complete validation system with mempool management
- Merkle Trees: Efficient transaction verification in blocks

Installation

bash
pip install -r requirements.txt
```

Project Structure

```
xorcoin/
├── xorcoin/
│   ├── core/           # Core data structures and blockchain logic
│   ├── crypto/         # Cryptographic operations
│   ├── validation/     # Transaction validation
│   ├── network/        # Networking and server components
│   └── system.py       # Main Xorcoin system
├── examples/           # Usage examples
└── tests/             # Test suite
```

Quick Start

```python
from xorcoin.system import XorcoinSystem
from xorcoin.crypto.keys import KeyManager

# Initialize the system
xorcoin = XorcoinSystem()

# Generate a keypair
key_manager = KeyManager()
private_key, public_key, address = key_manager.generate_keypair()

# Create and validate transactions
# See examples/demo.py for full usage
```

Usage Example

```python
# Initialize Xorcoin
from xorcoin import XorcoinSystem

system = XorcoinSystem()

# Generate keys
private_key, public_key, address = system.generate_wallet()

# Create a transaction
tx = system.create_transaction(
    inputs=[...],
    outputs=[...],
    private_key=private_key
)

# Validate and add to mempool
system.add_transaction(tx)

# Mine a block
block = system.mine_block()
```

Security Considerations

- Private keys are encrypted at rest using strong passwords
- All signatures use normalized low-S values to prevent malleability
- Network communication supports TLS encryption
- Implements replay protection across different chains

Requirements

- Python 3.8+
- cryptography
- ecdsa

Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

License

MIT License
