"""
Network message serialization for Xorcoin P2P protocol
"""

import base64
import json
from typing import Dict, Optional
from xorcoin.core.models import Block, Transaction, TxInput, TxOutput


class NetworkSerializer:
    """Handles serialization/deserialization for network messages"""
    
    @staticmethod
    def serialize_block(block: Block) -> dict:
        """Serialize block for network transmission"""
        return {
            'version': block.version,
            'height': block.height,
            'timestamp': block.timestamp,
            'prev_block_hash': block.prev_block_hash,
            'merkle_root': block.merkle_root,
            'difficulty': block.difficulty,
            'nonce': block.nonce,
            'transactions': [
                NetworkSerializer.serialize_transaction(tx) 
                for tx in block.transactions
            ]
        }
    
    @staticmethod
    def deserialize_block(data: dict) -> Optional[Block]:
        """Deserialize block from network data"""
        try:
            block = Block(
                version=data['version'],
                height=data['height'],
                timestamp=data['timestamp'],
                prev_block_hash=data['prev_block_hash'],
                merkle_root=data['merkle_root'],
                difficulty=data['difficulty'],
                nonce=data['nonce']
            )
            
            # Deserialize transactions
            for tx_data in data.get('transactions', []):
                tx = NetworkSerializer.deserialize_transaction(tx_data)
                if tx:
                    block.transactions.append(tx)
                    
            return block
        except Exception as e:
            print(f"Error deserializing block: {e}")
            return None
    
    @staticmethod
    def serialize_transaction(tx: Transaction) -> dict:
        """Serialize transaction for network transmission"""
        return {
            'version': tx.version,
            'chain_id': tx.chain_id,
            'inputs': [
                {
                    'prev_tx_hash': inp.prev_tx_hash,
                    'prev_output_index': inp.prev_output_index,
                    'signature': base64.b64encode(inp.signature).decode() if inp.signature else None,
                    'pubkey': base64.b64encode(inp.pubkey).decode() if inp.pubkey else None
                } for inp in tx.inputs
            ],
            'outputs': [
                {
                    'amount': out.amount,
                    'script_pubkey': out.script_pubkey
                } for out in tx.outputs
            ],
            'locktime': tx.locktime,
            'timestamp': tx.timestamp
        }
    
    @staticmethod
    def deserialize_transaction(data: dict) -> Optional[Transaction]:
        """Deserialize transaction from network data"""
        try:
            tx = Transaction(
                version=data['version'],
                chain_id=data['chain_id'],
                locktime=data.get('locktime', 0),
                timestamp=data.get('timestamp')
            )
            
            # Deserialize inputs
            for inp_data in data.get('inputs', []):
                tx_input = TxInput(
                    prev_tx_hash=inp_data['prev_tx_hash'],
                    prev_output_index=inp_data['prev_output_index']
                )
                
                if inp_data.get('signature'):
                    tx_input.signature = base64.b64decode(inp_data['signature'])
                if inp_data.get('pubkey'):
                    tx_input.pubkey = base64.b64decode(inp_data['pubkey'])
                    
                tx.inputs.append(tx_input)
            
            # Deserialize outputs
            for out_data in data.get('outputs', []):
                tx_output = TxOutput(
                    amount=out_data['amount'],
                    script_pubkey=out_data['script_pubkey']
                )
                tx.outputs.append(tx_output)
                
            return tx
        except Exception as e:
            print(f"Error deserializing transaction: {e}")
            return None
