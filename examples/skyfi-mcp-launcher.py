#!/usr/bin/env python3
"""
All-in-one SkyFi MCP launcher
Put your configuration directly in this file, then point Claude Desktop to it.
"""

import os
import sys
import json
import subprocess
import threading

# === CONFIGURATION - EDIT THESE VALUES ===
SKYFI_API_KEY = "sk-your-api-key-here"  # <-- Put your API key here
AWS_HOST = "your-instance.amazonaws.com"  # <-- Put your AWS host here
AWS_USER = "ec2-user"  # <-- Change if using different user
# ========================================

def forward_stdin_to_process(process, api_key):
    """Read from stdin, inject API key, and forward to MCP process."""
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                
                # Inject API key into request metadata
                if 'method' in request:
                    if 'metadata' not in request:
                        request['metadata'] = {}
                    if 'headers' not in request['metadata']:
                        request['metadata']['headers'] = {}
                    
                    request['metadata']['headers']['X-Skyfi-Api-Key'] = api_key
                
                process.stdin.write(json.dumps(request) + '\n')
                process.stdin.flush()
                
            except json.JSONDecodeError:
                process.stdin.write(line)
                process.stdin.flush()
    except KeyboardInterrupt:
        pass
    finally:
        process.stdin.close()

def forward_process_to_stdout(process):
    """Forward MCP process output to stdout."""
    try:
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass

def main():
    if SKYFI_API_KEY == "sk-your-api-key-here":
        print("Error: Please edit this file and add your SkyFi API key", file=sys.stderr)
        sys.exit(1)
    
    if AWS_HOST == "your-instance.amazonaws.com":
        print("Error: Please edit this file and add your AWS instance hostname", file=sys.stderr)
        sys.exit(1)
    
    # Start SSH connection to MCP server
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        f'{AWS_USER}@{AWS_HOST}',
        'cd /home/ec2-user/mcp-skyfi && source venv/bin/activate && python -m mcp_skyfi'
    ]
    
    try:
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Create threads for bidirectional communication
        stdin_thread = threading.Thread(
            target=forward_stdin_to_process,
            args=(process, SKYFI_API_KEY),
            daemon=True
        )
        stdout_thread = threading.Thread(
            target=forward_process_to_stdout,
            args=(process,),
            daemon=True
        )
        
        stdin_thread.start()
        stdout_thread.start()
        
        # Forward stderr
        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
        
        process.wait()
        
    except KeyboardInterrupt:
        process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start MCP server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()