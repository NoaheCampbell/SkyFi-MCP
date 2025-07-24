#!/usr/bin/env python3
"""
TCP server wrapper for MCP - runs on the server machine
"""
import socket
import subprocess
import os
import threading
import sys

def handle_client(client_socket, client_address):
    """Handle a client connection"""
    print(f"Connection from {client_address}", file=sys.stderr)
    
    # Start MCP server process
    env = os.environ.copy()
    # Add any environment variables from client if needed
    
    process = subprocess.Popen(
        ['python3', '-m', 'mcp_skyfi'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        env=env
    )
    
    # Forward data between socket and process
    def forward_input():
        while True:
            data = client_socket.recv(4096)
            if not data:
                process.stdin.close()
                break
            process.stdin.write(data)
            process.stdin.flush()
    
    def forward_output():
        while True:
            data = process.stdout.read(4096)
            if not data:
                break
            client_socket.send(data)
    
    # Start forwarding threads
    input_thread = threading.Thread(target=forward_input)
    output_thread = threading.Thread(target=forward_output)
    
    input_thread.start()
    output_thread.start()
    
    # Wait for completion
    input_thread.join()
    output_thread.join()
    
    process.wait()
    client_socket.close()
    print(f"Connection from {client_address} closed", file=sys.stderr)

def main():
    host = '0.0.0.0'  # Listen on all interfaces
    port = int(os.environ.get('MCP_TCP_PORT', '5000'))
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"MCP TCP server listening on {host}:{port}", file=sys.stderr)
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # Handle each client in a new thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()