#!/usr/bin/env python3
"""
Remote wrapper for MCP server - connects to remote server via TCP
"""
import socket
import sys
import os
import select

def forward_stdio_to_tcp(host, port):
    """Forward stdin/stdout to TCP connection"""
    # Connect to remote server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    # Set up non-blocking I/O
    sock.setblocking(False)
    
    while True:
        # Check for data to read
        readable, _, _ = select.select([sys.stdin.buffer, sock], [], [], 0.1)
        
        for stream in readable:
            if stream == sys.stdin.buffer:
                # Forward stdin to socket
                data = sys.stdin.buffer.read(4096)
                if data:
                    sock.send(data)
                else:
                    # EOF on stdin
                    sock.shutdown(socket.SHUT_WR)
                    
            elif stream == sock:
                # Forward socket to stdout
                try:
                    data = sock.recv(4096)
                    if data:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                    else:
                        # Connection closed
                        return
                except BlockingIOError:
                    pass

if __name__ == "__main__":
    # Get connection details from environment or args
    host = os.environ.get('MCP_REMOTE_HOST', '192.168.1.220')
    port = int(os.environ.get('MCP_REMOTE_PORT', '5000'))
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    try:
        forward_stdio_to_tcp(host, port)
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)