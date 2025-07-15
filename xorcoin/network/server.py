"""
Network server for Xorcoin
"""

import ssl
import socket
import json
import threading
from typing import Callable, Optional


class XorcoinServer:
    """Secure server for Xorcoin network communication"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8443):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.message_handler: Optional[Callable] = None
        
    def setup_ssl(self, certfile: str, keyfile: str) -> None:
        """Setup SSL context for secure communication"""
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        
    def set_message_handler(self, handler: Callable) -> None:
        """Set the function to handle incoming messages"""
        self.message_handler = handler
        
    def start(self) -> None:
        """Start the server"""
        if not self.ssl_context:
            raise ValueError("SSL not configured. Call setup_ssl() first.")
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        self.running = True
        print(f"Xorcoin server listening on {self.host}:{self.port}")
        
        # Accept connections in a separate thread
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.start()
        
    def stop(self) -> None:
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            
    def _accept_connections(self) -> None:
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                    
    def _handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle a client connection"""
        try:
            with self.ssl_context.wrap_socket(client_socket, server_side=True) as ssl_socket:
                print(f"Client connected from {address}")
                
                while self.running:
                    data = ssl_socket.recv(4096)
                    if not data:
                        break
                        
                    # Process the message
                    response = self._process_message(data)
                    
                    # Send response
                    ssl_socket.sendall(response)
                    
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Client {address} disconnected")
            
    def _process_message(self, data: bytes) -> bytes:
        """Process incoming message and return response"""
        try:
            # Decode message
            message = json.loads(data.decode())
            
            # Call message handler if set
            if self.message_handler:
                response = self.message_handler(message)
            else:
                response = {"status": "error", "message": "No handler configured"}
                
            return json.dumps(response).encode()
            
        except json.JSONDecodeError:
            return json.dumps({
                "status": "error",
                "message": "Invalid JSON"
            }).encode()
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }).encode()


class XorcoinClient:
    """Client for connecting to Xorcoin nodes"""
    
    def __init__(self, host: str, port: int = 8443):
        self.host = host
        self.port = port
        self.ssl_context: Optional[ssl.SSLContext] = None
        
    def setup_ssl(self, cafile: str) -> None:
        """Setup SSL context for secure communication"""
        self.ssl_context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, 
            cafile=cafile
        )
        
    def send_message(self, message: dict) -> dict:
        """Send a message to the server and get response"""
        if not self.ssl_context:
            raise ValueError("SSL not configured. Call setup_ssl() first.")
            
        sock = socket.create_connection((self.host, self.port))
        
        with self.ssl_context.wrap_socket(sock, server_hostname=self.host) as ssl_sock:
            # Send message
            data = json.dumps(message).encode()
            ssl_sock.sendall(data)
            
            # Receive response
            response_data = ssl_sock.recv(4096)
            return json.loads(response_data.decode())
            
    def ping(self) -> bool:
        """Ping the server to check if it's alive"""
        try:
            response = self.send_message({"type": "ping"})
            return response.get("status") == "ok"
        except Exception:
            return False
