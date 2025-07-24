#!/usr/bin/env python3
"""
HTTP client wrapper for MCP - converts STDIO to HTTP requests
"""
import sys
import os
import json
import requests
import threading
from queue import Queue

def read_jsonrpc_message(stream):
    """Read a JSON-RPC message from stream"""
    buffer = ""
    while True:
        char = stream.read(1)
        if not char:
            return None
        buffer += char
        
        # Try to parse as JSON
        try:
            message = json.loads(buffer)
            return message
        except json.JSONDecodeError:
            # Keep reading
            continue

def stdio_to_http_bridge(url):
    """Bridge STDIO to HTTP"""
    # Get environment variables to pass as headers
    headers = {}
    for key, value in os.environ.items():
        if key.startswith('SKYFI_'):
            headers[f'X-Env-{key}'] = value
    
    while True:
        try:
            # Read from stdin
            line = sys.stdin.readline()
            if not line:
                break
                
            # Send to HTTP endpoint
            response = requests.post(
                url, 
                data=line.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            
            # Write response to stdout
            sys.stdout.write(response.text)
            sys.stdout.flush()
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: http-client-wrapper.py <url>", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    stdio_to_http_bridge(url)