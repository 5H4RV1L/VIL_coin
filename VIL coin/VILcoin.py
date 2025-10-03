#!/usr/bin/env python3

import hashlib
import json
import time
import socket
import threading
import os
import pickle
import subprocess
import ipaddress
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Set
import getpass

# Color codes for CLI
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored_print(text, color):
    print(f"{color}{text}{Colors.ENDC}")

def generate_user_id():
    """Generate a random 10-character alphanumeric ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float, timestamp: float = None, tx_type: str = "transfer"):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.tx_type = tx_type  # "transfer" or "mining_reward"
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        transaction_string = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}{self.tx_type}"
        return hashlib.sha256(transaction_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'tx_type': self.tx_type,
            'hash': self.hash
        }

class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, miner: str = None):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.miner = miner
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        block_string = f"{self.index}{self.timestamp}{json.dumps([t.to_dict() for t in self.transactions])}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [t.to_dict() for t in self.transactions],
            'previous_hash': self.previous_hash,
            'miner': self.miner,
            'nonce': self.nonce,
            'hash': self.hash
        }

class User:
    def __init__(self, username: str, password: str, user_id: str = None):
        self.username = username
        self.user_id = user_id or generate_user_id()
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.balance = 1000.0
    
    def verify_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'user_id': self.user_id,
            'password_hash': self.password_hash,
            'balance': self.balance
        }

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 5  # Increased difficulty
        self.pending_transactions = []
        self.mining_reward = 2  # Reduced mining reward
        self.users = {}
        self.username_to_id = {}  # Map username to user_id
        self.id_to_username = {}  # Map user_id to username
        self.current_user = None
        self.peers = set()
        self.server_port = 8888
        self.my_ip = self.get_local_ip()
        self.sync_lock = threading.Lock()
        
        colored_print(f"📡 Node IP: {self.my_ip}", Colors.OKCYAN)
        
        self.load_data()

        # Validate local chain on startup
        if not self.is_chain_valid():
            colored_print("⚠️  Local chain validation failed on startup!", Colors.FAIL)
            threading.Thread(target=self.delayed_recovery, daemon=True).start()

        self.start_network_server()
        
        threading.Thread(target=self.auto_discover_and_sync, daemon=True).start()
    
    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_network_ranges(self) -> List[str]:
        """Get multiple network ranges for comprehensive scanning"""
        ip = ipaddress.ip_address(self.my_ip)
        ranges = []
        
        if ip.is_private:
            # Add /24 subnet
            network_24 = ipaddress.ip_network(f"{self.my_ip}/24", strict=False)
            ranges.append(str(network_24))
            
            # Add /16 subnet for broader discovery (sample it)
            try:
                network_16 = ipaddress.ip_network(f"{self.my_ip}/16", strict=False)
                ranges.append(str(network_16))
            except:
                pass
        
        return ranges
    
    def scan_for_peers(self) -> Set[str]:
        """Enhanced peer discovery with broader scanning"""
        peers = set()
        network_ranges = self.get_network_ranges()
        
        if not network_ranges:
            return peers
        
        colored_print("🔍 Scanning network for blockchain nodes...", Colors.OKCYAN)
        
        def check_peer(ip_str):
            if ip_str == self.my_ip:
                return
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)  # Faster timeout for broader scanning
                result = sock.connect_ex((ip_str, self.server_port))
                if result == 0:
                    message = {"type": "ping", "data": "discovery"}
                    sock.send(json.dumps(message).encode())
                    response = sock.recv(1024).decode()
                    if "pong" in response:
                        peers.add(ip_str)
                        colored_print(f"✅ Found peer: {ip_str}", Colors.OKGREEN)
                sock.close()
            except:
                pass
        
        threads = []
        total_ips_to_scan = 0
        
        for network_range in network_ranges:
            network = ipaddress.ip_network(network_range)
            hosts = list(network.hosts())
            
            # For /16 networks, sample random IPs instead of scanning all
            if network.prefixlen == 16:
                hosts = random.sample(hosts, min(200, len(hosts)))
            elif network.prefixlen == 24:
                hosts = hosts[:254]  # Scan all /24 hosts
            
            total_ips_to_scan += len(hosts)
            
            for ip in hosts:
                thread = threading.Thread(target=check_peer, args=(str(ip),))
                threads.append(thread)
                thread.start()
                
                # Limit concurrent threads
                if len(threads) >= 100:
                    for t in threads:
                        t.join()
                    threads = []
        
        # Join remaining threads
        for thread in threads:
            thread.join()
        
        colored_print(f"📊 Scanned {total_ips_to_scan} IP addresses", Colors.OKBLUE)
        return peers
    
    def auto_discover_and_sync(self):
        """Auto-discover peers and perform initial sync"""
        time.sleep(2)
        
        discovered_peers = self.scan_for_peers()
        for peer in discovered_peers:
            self.peers.add(peer)
        
        if self.peers:
            colored_print(f"🌐 Discovered {len(self.peers)} peers: {list(self.peers)}", Colors.OKGREEN)
            self.sync_with_network()
        else:
            colored_print("⚠️  No peers found on the network.", Colors.WARNING)
    
    def sync_with_network(self):
        """Synchronize with all network peers"""
        colored_print("🔄 SYNCHRONIZING WITH NETWORK", Colors.HEADER)
        
        with self.sync_lock:
            self.sync_user_lists()
            self.sync_blockchain_data()
            colored_print("✅ Network synchronization completed!", Colors.OKGREEN)
    
    def sync_user_lists(self):
        """Sync user lists with all peers"""
        colored_print("👥 Syncing user lists...", Colors.OKBLUE)
        
        for peer_ip in self.peers.copy():
            try:
                message = {"type": "request_users", "data": {}}
                response = self.send_message_with_response(peer_ip, message)
                
                if response and response.get('type') == 'users_response':
                    peer_users = response.get('data', {})
                    
                    for username, user_data in peer_users.items():
                        if username not in self.users:
                            user = User(username, "")
                            user.user_id = user_data.get('user_id', generate_user_id())
                            user.password_hash = user_data['password_hash']
                            user.balance = user_data['balance']
                            self.users[username] = user
                            self.username_to_id[username] = user.user_id
                            self.id_to_username[user.user_id] = username
                            colored_print(f"➕ Added user from peer: {username} (ID: {user.user_id})", Colors.OKGREEN)
            except Exception as e:
                colored_print(f"❌ Failed to sync users with {peer_ip}: {e}", Colors.FAIL)
                self.peers.discard(peer_ip)
    
    def sync_blockchain_data(self):
        """Sync blockchain data and implement consensus"""
        colored_print("⛓️  Syncing blockchain data...", Colors.OKBLUE)
        
        # Check if local chain is valid first
        if not self.is_valid_chain(self.chain):
            colored_print("⚠️  Local chain is invalid! Attempting recovery...", Colors.WARNING)
            if self.recover_from_invalid_chain():
                return  # Recovery successful, chain replaced
            # If recovery failed, continue with empty/genesis chain
        
        valid_chains = [(len(self.chain), self.chain, "local")]
        
        for peer_ip in self.peers.copy():
            try:
                message = {"type": "request_blockchain", "data": {}}
                response = self.send_message_with_response(peer_ip, message)
                
                if response and response.get('type') == 'blockchain_response':
                    peer_chain_data = response.get('data', [])
                    peer_chain = self.deserialize_chain(peer_chain_data)
                    
                    if peer_chain and self.is_valid_chain(peer_chain):
                        valid_chains.append((len(peer_chain), peer_chain, peer_ip))
                        colored_print(f"✅ Received valid chain from {peer_ip} (length: {len(peer_chain)})", Colors.OKGREEN)
                    else:
                        colored_print(f"❌ Invalid chain received from {peer_ip}", Colors.FAIL)
            except Exception as e:
                colored_print(f"❌ Failed to sync blockchain with {peer_ip}: {e}", Colors.FAIL)
                self.peers.discard(peer_ip)
        
        if valid_chains:
            valid_chains.sort(key=lambda x: x[0], reverse=True)
            longest_chain_length, longest_chain, source = valid_chains[0]
            
            if source != "local" and longest_chain_length > len(self.chain):
                colored_print(f"🔄 Adopting longer chain from {source} (length: {longest_chain_length})", Colors.WARNING)
                self.chain = longest_chain
                self.pending_transactions = []
                self.save_data()
            elif source == "local":
                colored_print(f"✅ Local chain is up to date (length: {longest_chain_length})", Colors.OKGREEN)
            else:
                colored_print(f"✅ Local chain is already the longest (length: {len(self.chain)})", Colors.OKGREEN)

    def deserialize_chain(self, chain_data: List[dict]) -> List[Block]:
        """Convert chain data back to Block objects"""
        try:
            chain = []
            for block_data in chain_data:
                transactions = []
                for tx_data in block_data['transactions']:
                    tx = Transaction(
                        tx_data['sender'],
                        tx_data['receiver'],
                        tx_data['amount'],
                        tx_data['timestamp'],
                        tx_data.get('tx_type', 'transfer')
                    )
                    transactions.append(tx)
                
                block = Block(
                    block_data['index'],
                    transactions,
                    block_data['previous_hash'],
                    block_data.get('miner')
                )
                block.nonce = block_data['nonce']
                block.hash = block_data['hash']
                block.timestamp = block_data['timestamp']
                chain.append(block)
            
            return chain
        except Exception as e:
            colored_print(f"❌ Error deserializing chain: {e}", Colors.FAIL)
            return None
    
    def is_valid_chain(self, chain: List[Block]) -> bool:
        """Validate a blockchain"""
        if not chain or len(chain) == 0:
            return False
        
        if chain[0].index != 0 or chain[0].previous_hash != "0":
            return False
        
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if current_block.index != previous_block.index + 1:
                return False
        
        return True
    
    def recover_from_invalid_chain(self):
        """Recover from an invalid local chain by adopting the longest valid chain from network"""
        colored_print("⚠️  WARNING: Local chain is invalid!", Colors.FAIL)
        colored_print("🔍 Searching network for valid chains to recover...", Colors.WARNING)

        if not self.peers:
            colored_print("❌ No peers available for recovery. Resetting to genesis block.", Colors.FAIL)
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.save_data()
            return False

        valid_chains = []

        for peer_ip in self.peers.copy():
            try:
                message = {"type": "request_blockchain", "data": {}}
                response = self.send_message_with_response(peer_ip, message, timeout=15)

                if response and response.get('type') == 'blockchain_response':
                    peer_chain_data = response.get('data', [])
                    peer_chain = self.deserialize_chain(peer_chain_data)

                    if peer_chain and self.is_valid_chain(peer_chain):
                        valid_chains.append((len(peer_chain), peer_chain, peer_ip))
                        colored_print(f"✅ Found valid chain from {peer_ip} (length: {len(peer_chain)})", Colors.OKGREEN)
                    else:
                        colored_print(f"❌ Invalid chain from {peer_ip}", Colors.FAIL)
            except Exception as e:
                colored_print(f"❌ Failed to get chain from {peer_ip}: {e}", Colors.FAIL)
                self.peers.discard(peer_ip)

        if valid_chains:
            # Sort by length and adopt the longest valid chain
            valid_chains.sort(key=lambda x: x[0], reverse=True)
            longest_chain_length, longest_chain, source = valid_chains[0]

            colored_print(f"🔄 RECOVERING: Adopting valid chain from {source} (length: {longest_chain_length})", Colors.OKGREEN)
            self.chain = longest_chain
            self.pending_transactions = []
            self.save_data()

            colored_print("✅ Chain recovered successfully!", Colors.OKGREEN)
            return True
        else:
            colored_print("❌ No valid chains found in network. Resetting to genesis block.", Colors.FAIL)
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.save_data()
            return False
        
    def delayed_recovery(self):
        """Delay recovery to allow network initialization"""
        time.sleep(3)  # Wait for network to initialize
        self.recover_from_invalid_chain()
    
    def send_message_with_response(self, peer_ip: str, message: dict, timeout: int = 10) -> dict:
        """Send message to peer and wait for response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((peer_ip, self.server_port))
            sock.send(json.dumps(message).encode())

            # Receive data in chunks until complete
            response_data = b""
            while True:
                chunk = sock.recv(65536)  # Larger buffer: 64KB chunks
                if not chunk:
                    break
                response_data += chunk
                # Check if we have a complete JSON (simple heuristic)
                try:
                    json.loads(response_data.decode())
                    break  # Complete JSON received
                except json.JSONDecodeError:
                    continue  # Keep receiving
                
            sock.close()

            return json.loads(response_data.decode())
        except Exception as e:
            raise Exception(f"Communication error: {e}")
    
    def create_genesis_block(self) -> Block:
        return Block(0, [], "0")
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def create_user(self, username: str, password: str) -> bool:
        if username in self.users:
            return False
        
        user = User(username, password)
        self.users[username] = user
        self.username_to_id[username] = user.user_id
        self.id_to_username[user.user_id] = username
        self.save_data()
        
        self.broadcast_user_update()
        return True
    
    def login(self, username: str, password: str) -> bool:
        if username not in self.users:
            return False
        
        if self.users[username].verify_password(password):
            self.current_user = username
            return True
        return False
    
    def logout(self):
        self.current_user = None
    
    def get_balance(self, username: str) -> float:
        balance = 0
        if username in self.users:
            balance = self.users[username].balance
        
        user_id = self.username_to_id.get(username)
        if not user_id:
            return balance
        
        # Calculate balance from blockchain transactions
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == user_id:
                    balance -= transaction.amount
                if transaction.receiver == user_id:
                    balance += transaction.amount
        
        return balance
    
    def create_transaction(self, sender: str, receiver: str, amount: float) -> bool:
        if sender not in self.users or receiver not in self.users:
            return False
        
        sender_balance = self.get_balance(sender)
        if sender_balance < amount:
            return False
        
        sender_id = self.username_to_id[sender]
        receiver_id = self.username_to_id[receiver]
        
        transaction = Transaction(sender_id, receiver_id, amount)
        self.pending_transactions.append(transaction)
        
        self.broadcast_transaction(transaction)
        self.save_data()
        return True
    
    def mine_pending_transactions(self, miner: str) -> bool:
        if not self.pending_transactions:
            return False
        
        valid_transactions = []
        current_balances = {}
        
        # Initialize balances
        for username in self.users:
            current_balances[self.username_to_id[username]] = self.get_balance(username)
        
        sorted_transactions = sorted(self.pending_transactions, key=lambda tx: tx.timestamp)
        
        # Validate transactions
        for tx in sorted_transactions:
            sender_username = self.id_to_username.get(tx.sender)
            receiver_username = self.id_to_username.get(tx.receiver)
            
            if (tx.sender in current_balances and 
                tx.receiver in current_balances and 
                current_balances[tx.sender] >= tx.amount):
                
                valid_transactions.append(tx)
                current_balances[tx.sender] -= tx.amount
                current_balances[tx.receiver] += tx.amount
            else:
                if sender_username and receiver_username:
                    colored_print(f"⚠️  Skipping invalid transaction: {sender_username} -> {receiver_username}: {tx.amount} (insufficient funds)", Colors.WARNING)
        
        if not valid_transactions:
            colored_print("❌ No valid transactions to mine!", Colors.FAIL)
            return False
        
        # Add mining reward transaction
        miner_id = self.username_to_id[miner]
        reward_tx = Transaction("SYSTEM", miner_id, self.mining_reward, tx_type="mining_reward")
        valid_transactions.append(reward_tx)
        
        colored_print(f"⛏️  Mining {len(valid_transactions)-1} valid transactions + 1 reward transaction...", Colors.OKCYAN)
        
        block = Block(
            len(self.chain),
            valid_transactions,
            self.get_latest_block().hash,
            miner_id
        )
        
        colored_print(f"🔨 Mining block #{block.index}... Please wait.", Colors.WARNING)
        start_time = time.time()
        block.mine_block(self.difficulty)
        end_time = time.time()
        
        self.chain.append(block)
        
        # Remove mined transactions from pending
        mined_hashes = {tx.hash for tx in valid_transactions if tx.tx_type != "mining_reward"}
        self.pending_transactions = [
            tx for tx in self.pending_transactions 
            if tx.hash not in mined_hashes
        ]
        
        colored_print(f"✅ Block mined successfully in {end_time - start_time:.2f} seconds!", Colors.OKGREEN)
        colored_print(f"🔗 Block hash: {block.hash[:20]}...", Colors.OKBLUE)
        colored_print(f"💰 Miner reward: {self.mining_reward} VIL coins", Colors.OKGREEN)
        colored_print(f"📦 Transactions included: {len(valid_transactions)-1}", Colors.OKBLUE)
        colored_print(f"⏳ Remaining pending: {len(self.pending_transactions)}", Colors.OKBLUE)
        
        self.save_data()
        self.broadcast_block(block)
        return True
    
    def search_block_by_number(self, block_number: int) -> Optional[Block]:
        """Search for a block by its number"""
        if 0 <= block_number < len(self.chain):
            return self.chain[block_number]
        return None
    
    def is_chain_valid(self) -> bool:
        return self.is_valid_chain(self.chain)
    
    def save_data(self):
        data = {
            'chain': [block.to_dict() for block in self.chain],
            'users': {username: user.to_dict() for username, user in self.users.items()},
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions]
        }
        
        with open('blockchain_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        if os.path.exists('blockchain_data.json'):
            try:
                with open('blockchain_data.json', 'r') as f:
                    data = json.load(f)
                
                # Load chain
                self.chain = []
                for block_data in data.get('chain', []):
                    transactions = []
                    for tx_data in block_data['transactions']:
                        tx = Transaction(
                            tx_data['sender'],
                            tx_data['receiver'],
                            tx_data['amount'],
                            tx_data['timestamp'],
                            tx_data.get('tx_type', 'transfer')
                        )
                        transactions.append(tx)
                    
                    block = Block(
                        block_data['index'],
                        transactions,
                        block_data['previous_hash'],
                        block_data.get('miner')
                    )
                    block.nonce = block_data['nonce']
                    block.hash = block_data['hash']
                    block.timestamp = block_data['timestamp']
                    self.chain.append(block)
                
                # Load users
                for username, user_data in data.get('users', {}).items():
                    user = User(username, "") 
                    user.user_id = user_data.get('user_id', generate_user_id())
                    user.password_hash = user_data['password_hash']
                    user.balance = user_data['balance']
                    self.users[username] = user
                    self.username_to_id[username] = user.user_id
                    self.id_to_username[user.user_id] = username
                
                # Load pending transactions
                self.pending_transactions = []
                for tx_data in data.get('pending_transactions', []):
                    tx = Transaction(
                        tx_data['sender'],
                        tx_data['receiver'],
                        tx_data['amount'],
                        tx_data['timestamp'],
                        tx_data.get('tx_type', 'transfer')
                    )
                    self.pending_transactions.append(tx)
                
            except Exception as e:
                colored_print(f"❌ Error loading data: {e}", Colors.FAIL)
                self.chain = [self.create_genesis_block()]
    
    def start_network_server(self):
        def server():
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('', self.server_port))
                server_socket.listen(10)  # Increased backlog for better reliability
                colored_print(f"🌐 Network server listening on port {self.server_port}", Colors.OKGREEN)
                
                while True:
                    client_socket, addr = server_socket.accept()
                    threading.Thread(target=self.handle_peer, args=(client_socket, addr)).start()
            except Exception as e:
                colored_print(f"❌ Server error: {e}", Colors.FAIL)
        
        threading.Thread(target=server, daemon=True).start()
    
    def handle_peer(self, client_socket, addr):
        try:
            # Receive data in chunks for large messages
            data_bytes = b""
            client_socket.settimeout(5)
            while True:
                try:
                    chunk = client_socket.recv(65536)  # 64KB chunks
                    if not chunk:
                        break
                    data_bytes += chunk
                    # Try to parse as complete JSON
                    try:
                        json.loads(data_bytes.decode())
                        break  # Complete JSON received
                    except json.JSONDecodeError:
                        continue  # Keep receiving
                except socket.timeout:
                    break  # No more data
                
            data = data_bytes.decode()
            if not data:
                return
                
            message = json.loads(data)
            peer_ip = addr[0]
            
            if peer_ip != self.my_ip:
                self.peers.add(peer_ip)
            
            if message['type'] == 'transaction':
                tx_data = message['data']
                tx = Transaction(
                    tx_data['sender'],
                    tx_data['receiver'],
                    tx_data['amount'],
                    tx_data['timestamp'],
                    tx_data.get('tx_type', 'transfer')
                )
                tx_exists = any(
                    existing_tx.hash == tx.hash 
                    for existing_tx in self.pending_transactions
                )
                if not tx_exists:
                    self.pending_transactions.append(tx)
                    sender_name = self.id_to_username.get(tx.sender, tx.sender)
                    receiver_name = self.id_to_username.get(tx.receiver, tx.receiver)
                    colored_print(f"📨 Received transaction: {sender_name} -> {receiver_name}: {tx.amount}", Colors.OKCYAN)
                    self.save_data()
            
            elif message['type'] == 'block':
                with self.sync_lock:
                    block_data = message['data']
                    colored_print(f"📦 Received new block #{block_data['index']} from {peer_ip}", Colors.OKCYAN)
                    
                    if block_data['index'] == len(self.chain):
                        transactions = []
                        for tx_data in block_data['transactions']:
                            tx = Transaction(
                                tx_data['sender'],
                                tx_data['receiver'],
                                tx_data['amount'],
                                tx_data['timestamp'],
                                tx_data.get('tx_type', 'transfer')
                            )
                            transactions.append(tx)
                        
                        new_block = Block(
                            block_data['index'],
                            transactions,
                            block_data['previous_hash'],
                            block_data.get('miner')
                        )
                        new_block.nonce = block_data['nonce']
                        new_block.hash = block_data['hash']
                        new_block.timestamp = block_data['timestamp']
                        
                        if (new_block.previous_hash == self.get_latest_block().hash and 
                            new_block.hash == new_block.calculate_hash()):
                            self.chain.append(new_block)
                            for tx in transactions:
                                self.pending_transactions = [
                                    ptx for ptx in self.pending_transactions 
                                    if ptx.hash != tx.hash
                                ]
                            colored_print(f"✅ Block #{block_data['index']} added to chain!", Colors.OKGREEN)
                            self.save_data()
                        else:
                            colored_print(f"❌ Invalid block received from {peer_ip}", Colors.FAIL)
            
            elif message['type'] == 'ping':
                response = {"type": "pong", "data": "alive"}
                client_socket.send(json.dumps(response).encode())
            
            elif message['type'] == 'request_users':
                users_data = {username: user.to_dict() for username, user in self.users.items()}
                response = {"type": "users_response", "data": users_data}
                client_socket.send(json.dumps(response).encode())
            
            elif message['type'] == 'request_blockchain':
                chain_data = [block.to_dict() for block in self.chain]
                response = {"type": "blockchain_response", "data": chain_data}
                client_socket.send(json.dumps(response).encode())
            
            elif message['type'] == 'user_update':
                user_data = message['data']
                username = user_data['username']
                if username not in self.users:
                    user = User(username, "")
                    user.user_id = user_data.get('user_id', generate_user_id())
                    user.password_hash = user_data['password_hash']
                    user.balance = user_data['balance']
                    self.users[username] = user
                    self.username_to_id[username] = user.user_id
                    self.id_to_username[user.user_id] = username
                    colored_print(f"➕ Added new user from network: {username} (ID: {user.user_id})", Colors.OKGREEN)
                    self.save_data()
            
        except Exception as e:
            colored_print(f"❌ Error handling peer {addr[0]}: {e}", Colors.FAIL)
        finally:
            client_socket.close()
    
    def add_peer(self, ip: str):
        self.peers.add(ip)
    
    def broadcast_transaction(self, transaction: Transaction):
        message = {
            'type': 'transaction',
            'data': transaction.to_dict()
        }
        self.broadcast_message(message)
        colored_print(f"📡 Broadcasting transaction to {len(self.peers)} peers", Colors.OKCYAN)
    
    def broadcast_block(self, block: Block):
        message = {
            'type': 'block',
            'data': block.to_dict()
        }
        self.broadcast_message(message)
        colored_print(f"📡 Broadcasting new block to {len(self.peers)} peers", Colors.OKCYAN)
    
    def broadcast_user_update(self):
        if self.current_user and self.current_user in self.users:
            message = {
                'type': 'user_update',
                'data': self.users[self.current_user].to_dict()
            }
            self.broadcast_message(message)
    
    def broadcast_message(self, message: dict):
        failed_peers = set()
        for peer_ip in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((peer_ip, self.server_port))
                sock.send(json.dumps(message).encode())
                sock.close()
            except Exception as e:
                colored_print(f"❌ Failed to send message to {peer_ip}: {e}", Colors.FAIL)
                failed_peers.add(peer_ip)
        
        self.peers -= failed_peers

class BlockchainCLI:
    def __init__(self):
        self.blockchain = Blockchain()
        colored_print("=" * 50, Colors.HEADER)
        colored_print("🪙  VIL COIN BLOCKCHAIN NETWORK  🪙", Colors.HEADER)
        colored_print("=" * 50, Colors.HEADER)
        colored_print("✅ Blockchain initialized successfully!", Colors.OKGREEN)
        colored_print(f"🌐 Network server started on port {self.blockchain.server_port}", Colors.OKGREEN)
        
    def show_menu(self):
        print()
        if self.blockchain.current_user:
            user_id = self.blockchain.users[self.blockchain.current_user].user_id
            colored_print(f"👤 LOGGED IN AS: {self.blockchain.current_user} (ID: {user_id})", Colors.HEADER)
            colored_print("=" * 50, Colors.HEADER)
            print(f"{Colors.OKGREEN}1.{Colors.ENDC} 💰 Show Balance")
            print(f"{Colors.OKGREEN}2.{Colors.ENDC} 💸 Send VIL Coins")
            print(f"{Colors.OKGREEN}3.{Colors.ENDC} ⛏️  Mine Block")
            print(f"{Colors.OKGREEN}4.{Colors.ENDC} 📖 Show Recent Transactions")
            print(f"{Colors.OKGREEN}5.{Colors.ENDC} 🔍 Search Block by Number")
            print(f"{Colors.OKGREEN}6.{Colors.ENDC} ⏳ Show Pending Transactions")
            print(f"{Colors.OKGREEN}7.{Colors.ENDC} 👥 Show All Users")
            print(f"{Colors.OKGREEN}8.{Colors.ENDC} 🌐 Show Network Peers")
            print(f"{Colors.OKGREEN}9.{Colors.ENDC} 🔄 Sync with Network")
            print(f"{Colors.OKGREEN}10.{Colors.ENDC} ➕ Add Manual Peer")
            print(f"{Colors.OKGREEN}11.{Colors.ENDC} 🚪 Logout")
            print(f"{Colors.OKGREEN}12.{Colors.ENDC} 🚫 Exit")
        else:
            colored_print("🏠 MAIN MENU", Colors.HEADER)
            colored_print("=" * 50, Colors.HEADER)
            print(f"{Colors.OKGREEN}1.{Colors.ENDC} 👤 Create Account")
            print(f"{Colors.OKGREEN}2.{Colors.ENDC} 🔑 Login")
            print(f"{Colors.OKGREEN}3.{Colors.ENDC} 🌐 Show Network Peers")
            print(f"{Colors.OKGREEN}4.{Colors.ENDC} 🔄 Sync with Network")
            print(f"{Colors.OKGREEN}5.{Colors.ENDC} 🚫 Exit")
    
    def create_account(self):
        print()
        colored_print("👤 CREATE NEW ACCOUNT", Colors.HEADER)
        colored_print("=" * 30, Colors.HEADER)
        username = input(f"{Colors.OKCYAN}Enter username: {Colors.ENDC}").strip()
        if not username:
            colored_print("❌ Username cannot be empty!", Colors.FAIL)
            return
        
        password = getpass.getpass(f"{Colors.OKCYAN}Enter password: {Colors.ENDC}")
        if not password:
            colored_print("❌ Password cannot be empty!", Colors.FAIL)
            return
        
        if self.blockchain.create_user(username, password):
            user_id = self.blockchain.users[username].user_id
            colored_print(f"✅ Account created successfully!", Colors.OKGREEN)
            colored_print(f"🆔 Your User ID: {user_id}", Colors.OKBLUE)
            colored_print(f"💰 You received 1000 initial VIL coins!", Colors.OKGREEN)
        else:
            colored_print("❌ Username already exists!", Colors.FAIL)
    
    def login(self):
        print()
        colored_print("🔑 LOGIN TO YOUR ACCOUNT", Colors.HEADER)
        colored_print("=" * 30, Colors.HEADER)
        username = input(f"{Colors.OKCYAN}Enter username: {Colors.ENDC}").strip()
        password = getpass.getpass(f"{Colors.OKCYAN}Enter password: {Colors.ENDC}")
        
        if self.blockchain.login(username, password):
            user_id = self.blockchain.users[username].user_id
            colored_print(f"✅ Welcome back, {username}! (ID: {user_id})", Colors.OKGREEN)
        else:
            colored_print("❌ Invalid username or password!", Colors.FAIL)
    
    def show_balance(self):
        if not self.blockchain.current_user:
            colored_print("❌ Please login first!", Colors.FAIL)
            return
        
        balance = self.blockchain.get_balance(self.blockchain.current_user)
        print()
        colored_print("💰 YOUR BALANCE", Colors.HEADER)
        colored_print("=" * 20, Colors.HEADER)
        colored_print(f"🪙  {balance:.2f} VIL coins", Colors.OKGREEN)
    
    def send_coins(self):
        if not self.blockchain.current_user:
            colored_print("❌ Please login first!", Colors.FAIL)
            return
        
        print()
        colored_print("💸 SEND VIL COINS", Colors.HEADER)
        colored_print("=" * 20, Colors.HEADER)
        receiver = input(f"{Colors.OKCYAN}Enter receiver username: {Colors.ENDC}").strip()
        
        if receiver == self.blockchain.current_user:
            colored_print("❌ You cannot send coins to yourself!", Colors.FAIL)
            return
        
        if receiver not in self.blockchain.users:
            colored_print("❌ Receiver not found!", Colors.FAIL)
            return
        
        try:
            amount = float(input(f"{Colors.OKCYAN}Enter amount: {Colors.ENDC}"))
            if amount <= 0:
                colored_print("❌ Amount must be positive!", Colors.FAIL)
                return
        except ValueError:
            colored_print("❌ Invalid amount!", Colors.FAIL)
            return
        
        current_balance = self.blockchain.get_balance(self.blockchain.current_user)
        if current_balance < amount:
            colored_print(f"❌ Insufficient funds! Your balance: {current_balance:.2f} VIL", Colors.FAIL)
            return
        
        if self.blockchain.create_transaction(self.blockchain.current_user, receiver, amount):
            receiver_id = self.blockchain.users[receiver].user_id
            colored_print(f"✅ Transaction created successfully!", Colors.OKGREEN)
            colored_print(f"💸 Sent {amount:.2f} VIL coins to {receiver} (ID: {receiver_id})", Colors.OKGREEN)
            colored_print("⏳ Transaction broadcasted and is pending. Mine a block to confirm it.", Colors.WARNING)
        else:
            colored_print("❌ Transaction failed!", Colors.FAIL)
    
    def mine_block(self):
        if not self.blockchain.current_user:
            colored_print("❌ Please login first!", Colors.FAIL)
            return
        
        print()
        colored_print("⛏️  MINE NEW BLOCK", Colors.HEADER)
        colored_print("=" * 20, Colors.HEADER)
        if not self.blockchain.pending_transactions:
            colored_print("❌ No pending transactions to mine!", Colors.FAIL)
            return
        
        colored_print(f"📦 Pending transactions: {len(self.blockchain.pending_transactions)}", Colors.OKBLUE)
        colored_print(f"💎 Mining difficulty: {self.blockchain.difficulty}", Colors.OKBLUE)
        colored_print(f"🏆 Mining reward: {self.blockchain.mining_reward} VIL coins", Colors.OKBLUE)
        
        confirm = input(f"{Colors.OKCYAN}Start mining? (y/n): {Colors.ENDC}").strip().lower()
        
        if confirm == 'y':
            if self.blockchain.mine_pending_transactions(self.blockchain.current_user):
                colored_print("🎉 Mining completed successfully!", Colors.OKGREEN)
            else:
                colored_print("❌ Mining failed!", Colors.FAIL)
    
    def show_recent_ledger(self):
        print()
        colored_print("📖 RECENT TRANSACTIONS (Last 10 Blocks)", Colors.HEADER)
        colored_print("=" * 50, Colors.HEADER)
        colored_print(f"⛓️  Chain length: {len(self.blockchain.chain)} blocks", Colors.OKBLUE)
        colored_print(f"✅ Chain valid: {self.blockchain.is_chain_valid()}", Colors.OKGREEN if self.blockchain.is_chain_valid() else Colors.FAIL)
        print("-" * 80)
        
        # Show last 10 blocks
        recent_blocks = self.blockchain.chain[-10:]
        
        for block in recent_blocks:
            colored_print(f"📦 Block #{block.index}", Colors.OKBLUE)
            timestamp_str = datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(f"🕒 Timestamp: {timestamp_str}")
            print(f"🔗 Previous Hash: {block.previous_hash[:20]}...")
            print(f"🔐 Hash: {block.hash[:20]}...")
            print(f"🎯 Nonce: {block.nonce}")
            
            if block.miner and block.miner != "0":
                miner_name = self.blockchain.id_to_username.get(block.miner, block.miner)
                colored_print(f"⛏️  Miner ID: {block.miner}", Colors.OKGREEN)
            
            if block.transactions:
                colored_print("💰 Transactions:", Colors.OKCYAN)
                for tx in block.transactions:
                    if tx.tx_type == "mining_reward":
                        colored_print(f"  🏆 MINING REWARD -> {tx.receiver}: {tx.amount:.2f} VIL", Colors.WARNING)
                    else:
                        print(f"  💸 {tx.sender} -> {tx.receiver}: {tx.amount:.2f} VIL")
            else:
                colored_print("💰 Transactions: Genesis Block", Colors.WARNING)
            
            print("-" * 80)
    
    def search_block(self):
        print()
        colored_print("🔍 SEARCH BLOCK BY NUMBER", Colors.HEADER)
        colored_print("=" * 30, Colors.HEADER)
        
        try:
            block_number = int(input(f"{Colors.OKCYAN}Enter block number (0-{len(self.blockchain.chain)-1}): {Colors.ENDC}"))
            block = self.blockchain.search_block_by_number(block_number)
            
            if block:
                print()
                colored_print(f"📦 BLOCK #{block.index} DETAILS", Colors.HEADER)
                print("-" * 40)
                timestamp_str = datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                print(f"🕒 Timestamp: {timestamp_str}")
                print(f"🔗 Previous Hash: {block.previous_hash}")
                print(f"🔐 Hash: {block.hash}")
                print(f"🎯 Nonce: {block.nonce}")
                
                if block.miner and block.miner != "0":
                    miner_name = self.blockchain.id_to_username.get(block.miner, block.miner)
                    colored_print(f"⛏️Miner ID: {block.miner}", Colors.OKGREEN)
                
                if block.transactions:
                    colored_print(f"💰 Transactions ({len(block.transactions)}):", Colors.OKCYAN)
                    for i, tx in enumerate(block.transactions, 1):
                        if tx.tx_type == "mining_reward":
                            colored_print(f"  {i}. 🏆 MINING REWARD -> {tx.receiver}: {tx.amount:.2f} VIL", Colors.WARNING)
                        else:
                            tx_time = datetime.fromtimestamp(tx.timestamp).strftime('%H:%M:%S')
                            print(f"  {i}. 💸 [{tx_time}] {tx.sender} -> {tx.receiver}: {tx.amount:.2f} VIL")
                else:
                    colored_print("💰 Transactions: Genesis Block", Colors.WARNING)
            else:
                colored_print(f"❌ Block #{block_number} not found!", Colors.FAIL)
                
        except ValueError:
            colored_print("❌ Please enter a valid block number!", Colors.FAIL)
    
    def show_pending_transactions(self):
        print()
        colored_print("⏳ PENDING TRANSACTIONS", Colors.HEADER)
        colored_print("=" * 30, Colors.HEADER)
        if not self.blockchain.pending_transactions:
            colored_print("✅ No pending transactions.", Colors.OKGREEN)
            return
        
        colored_print(f"📦 Total pending: {len(self.blockchain.pending_transactions)}", Colors.OKBLUE)
        print("-" * 60)
        
        for i, tx in enumerate(self.blockchain.pending_transactions, 1):
            timestamp_str = datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            sender_name = self.blockchain.id_to_username.get(tx.sender, tx.sender)
            receiver_name = self.blockchain.id_to_username.get(tx.receiver, tx.receiver)
            print(f"{i}. 🕒 {timestamp_str} | 💸 {sender_name} -> {receiver_name}: {tx.amount:.2f} VIL")
    
    def show_all_users(self):
        print()
        colored_print("👥 ALL REGISTERED USERS", Colors.HEADER)
        colored_print("=" * 30, Colors.HEADER)
        if not self.blockchain.users:
            colored_print("❌ No users registered.", Colors.FAIL)
            return
        
        colored_print(f"👤 Total users: {len(self.blockchain.users)}", Colors.OKBLUE)
        print("-" * 40)
        for username, user in self.blockchain.users.items():
            online_status = "🟢 ONLINE" if username == self.blockchain.current_user else "⚪ OFFLINE"
            colored_print(f"👤 {username} - {online_status}", Colors.OKGREEN if username == self.blockchain.current_user else Colors.ENDC)
        print("-" * 40)
    
    def show_peers(self):
        print()
        colored_print("🌐 NETWORK PEERS", Colors.HEADER)
        colored_print("=" * 20, Colors.HEADER)
        colored_print(f"📡 My IP: {self.blockchain.my_ip}", Colors.OKBLUE)
        if self.blockchain.peers:
            colored_print(f"🔗 Connected peers ({len(self.blockchain.peers)}):", Colors.OKGREEN)
            for i, peer in enumerate(self.blockchain.peers, 1):
                print(f"  {i}. 🌐 {peer}")
        else:
            colored_print("⚠️  No peers connected.", Colors.WARNING)
    
    def sync_with_network(self):
        print()
        colored_print("🔄 SYNC WITH NETWORK", Colors.HEADER)
        colored_print("=" * 25, Colors.HEADER)
        if not self.blockchain.peers:
            colored_print("🔍 No peers connected! Scanning for peers...", Colors.WARNING)
            discovered_peers = self.blockchain.scan_for_peers()
            for peer in discovered_peers:
                self.blockchain.peers.add(peer)
            
            if not self.blockchain.peers:
                colored_print("❌ No peers found on the network!", Colors.FAIL)
                return
        
        colored_print("🔄 Synchronizing with network peers...", Colors.OKCYAN)
        self.blockchain.sync_with_network()
    
    def add_manual_peer(self):
        print()
        colored_print("➕ ADD MANUAL PEER", Colors.HEADER)
        colored_print("=" * 25, Colors.HEADER)
        peer_ip = input(f"{Colors.OKCYAN}Enter peer IP address: {Colors.ENDC}").strip()
        if peer_ip:
            self.blockchain.add_peer(peer_ip)
            colored_print(f"✅ Added peer: {peer_ip}", Colors.OKGREEN)
            
            try:
                message = {"type": "ping", "data": "manual_add"}
                response = self.blockchain.send_message_with_response(peer_ip, message, timeout=5)
                if response and response.get('type') == 'pong':
                    colored_print(f"🟢 Peer {peer_ip} is reachable!", Colors.OKGREEN)
                    colored_print("🔄 Syncing with new peer...", Colors.OKCYAN)
                    self.blockchain.sync_with_network()
                else:
                    colored_print(f"⚠️  Warning: Peer {peer_ip} may not be reachable.", Colors.WARNING)
            except Exception as e:
                colored_print(f"⚠️  Warning: Could not verify peer {peer_ip}: {e}", Colors.WARNING)
        else:
            colored_print("❌ Invalid IP address!", Colors.FAIL)
    
    def run(self):
        while True:
            try:
                self.show_menu()
                choice = input(f"\n{Colors.OKCYAN}Enter your choice: {Colors.ENDC}").strip()
                
                if self.blockchain.current_user:
                    if choice == '1':
                        self.show_balance()
                    elif choice == '2':
                        self.send_coins()
                    elif choice == '3':
                        self.mine_block()
                    elif choice == '4':
                        self.show_recent_ledger()
                    elif choice == '5':
                        self.search_block()
                    elif choice == '6':
                        self.show_pending_transactions()
                    elif choice == '7':
                        self.show_all_users()
                    elif choice == '8':
                        self.show_peers()
                    elif choice == '9':
                        self.sync_with_network()
                    elif choice == '10':
                        self.add_manual_peer()
                    elif choice == '11':
                        self.blockchain.logout()
                        colored_print("👋 Logged out successfully!", Colors.OKGREEN)
                    elif choice == '12':
                        colored_print("👋 Goodbye! Thanks for using VIL Coin!", Colors.HEADER)
                        break
                    else:
                        colored_print("❌ Invalid choice! Please try again.", Colors.FAIL)
                else:
                    if choice == '1':
                        self.create_account()
                    elif choice == '2':
                        self.login()
                    elif choice == '3':
                        self.show_peers()
                    elif choice == '4':
                        self.sync_with_network()
                    elif choice == '5':
                        colored_print("👋 Goodbye! Thanks for using VIL Coin!", Colors.HEADER)
                        break
                    else:
                        colored_print("❌ Invalid choice! Please try again.", Colors.FAIL)
                        
            except KeyboardInterrupt:
                print()
                colored_print("👋 Goodbye! Thanks for using VIL Coin!", Colors.HEADER)
                break
            except Exception as e:
                colored_print(f"❌ An error occurred: {e}", Colors.FAIL)

if __name__ == "__main__":
    cli = BlockchainCLI()
    cli.run()