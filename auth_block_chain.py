import hashlib
import json
from datetime import datetime

class AuthBlockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = {
            'block_number': 0,
            'timestamp': str(datetime.now()),
            'data': 'Genesis Block - Banking MFA System',
            'previous_hash': '0',
            'hash': self.calculate_hash(0, str(datetime.now()), 'Genesis Block', '0')
        }
        self.chain.append(genesis_block)
    
    def calculate_hash(self, block_number, timestamp, data, previous_hash):
        """Calculate SHA-256 hash of a block"""
        block_string = f"{block_number}{timestamp}{data}{previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def add_auth_event(self, username, event_type, ip_address=None, device_info=None):
        """Add a new authentication event to the blockchain"""
        previous_block = self.chain[-1]
        new_block_number = previous_block['block_number'] + 1
        timestamp = str(datetime.now())
        
        # Hash sensitive data
        username_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16] if ip_address else "N/A"
        
        data = {
            'username_hash': username_hash,
            'event_type': event_type,
            'ip_hash': ip_hash,
            'device_info': device_info or 'unknown'
        }
        
        new_hash = self.calculate_hash(
            new_block_number, 
            timestamp, 
            json.dumps(data), 
            previous_block['hash']
        )
        
        new_block = {
            'block_number': new_block_number,
            'timestamp': timestamp,
            'data': data,
            'previous_hash': previous_block['hash'],
            'hash': new_hash
        }
        
        self.chain.append(new_block)
        return new_block
    
    def verify_chain(self):
        """Verify the integrity of the blockchain"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check current block hash
            calculated_hash = self.calculate_hash(
                current['block_number'],
                current['timestamp'],
                json.dumps(current['data']),
                current['previous_hash']
            )
            
            if current['hash'] != calculated_hash:
                return False, f"Block {i} has been tampered!"
            
            # Check link to previous block
            if current['previous_hash'] != previous['hash']:
                return False, f"Block {i} link is broken!"
        
        return True, "Blockchain is valid!"
    
    def get_user_history(self, username):
        """Get authentication history for a specific user"""
        username_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        
        user_blocks = [
            block for block in self.chain[1:]  # Skip genesis block
            if isinstance(block['data'], dict) and 
               block['data'].get('username_hash') == username_hash
        ]
        
        return user_blocks
