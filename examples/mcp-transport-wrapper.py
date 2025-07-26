#!/usr/bin/env python3
"""
MCP Transport Wrapper for SkyFi

This wrapper adds API key headers to all MCP requests before forwarding
them to the actual MCP server. This allows secure API key handling without
storing keys on the remote server.

Usage:
1. Set SKYFI_API_KEY in your local environment
2. Configure Claude Desktop to use this wrapper as the MCP command
3. The wrapper will inject the API key into all requests
"""

import os
import sys
import json
import subprocess
import threading
import logging

# Configuration
REMOTE_HOST = os.environ.get('MCP_SKYFI_HOST', 'your-aws-instance.com')
REMOTE_USER = os.environ.get('MCP_SKYFI_USER', 'ec2-user')
API_KEY = os.environ.get('SKYFI_API_KEY')

# Set up logging
if os.environ.get('DEBUG'):
    logging.basicConfig(level=logging.DEBUG, format='%(message)s', stream=sys.stderr)
else:
    logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)

if not API_KEY:
    print("Error: SKYFI_API_KEY environment variable is required", file=sys.stderr)
    sys.exit(1)

def forward_stdin_to_process(process):
    """Read from stdin, inject API key, and forward to MCP process."""
    try:
        for line in sys.stdin:
            try:
                # Parse JSON request
                request = json.loads(line.strip())
                
                # Inject API key into request metadata
                if 'method' in request:
                    if 'metadata' not in request:
                        request['metadata'] = {}
                    if 'headers' not in request['metadata']:
                        request['metadata']['headers'] = {}
                    
                    request['metadata']['headers']['X-Skyfi-Api-Key'] = API_KEY
                    
                    logger.debug(f"Injecting API key into request: {request['method']}")
                
                # Forward modified request
                process.stdin.write(json.dumps(request) + '\n')
                process.stdin.flush()
                
            except json.JSONDecodeError:
                # Not JSON, forward as-is
                process.stdin.write(line)
                process.stdin.flush()
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                
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
    """Main entry point."""
    # Build SSH command
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        f'{REMOTE_USER}@{REMOTE_HOST}',
        'cd /home/ec2-user/mcp-skyfi && source venv/bin/activate && python -m mcp_skyfi'
    ]
    
    logger.debug(f"Launching MCP server: {' '.join(ssh_cmd)}")
    
    try:
        # Start MCP process
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Create threads for bidirectional communication
        stdin_thread = threading.Thread(
            target=forward_stdin_to_process,
            args=(process,),
            daemon=True
        )
        stdout_thread = threading.Thread(
            target=forward_process_to_stdout,
            args=(process,),
            daemon=True
        )
        
        # Start threads
        stdin_thread.start()
        stdout_thread.start()
        
        # Forward stderr
        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
        
        # Wait for process to complete
        process.wait()
        
    except KeyboardInterrupt:
        logger.debug("Received interrupt, shutting down...")
        process.terminate()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()