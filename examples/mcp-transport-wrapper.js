#!/usr/bin/env node
/**
 * MCP Transport Wrapper for SkyFi
 * 
 * This wrapper adds API key headers to all MCP requests before forwarding
 * them to the actual MCP server. This allows secure API key handling without
 * storing keys on the remote server.
 * 
 * Usage:
 * 1. Set SKYFI_API_KEY in your local environment
 * 2. Configure Claude Desktop to use this wrapper as the MCP command
 * 3. The wrapper will inject the API key into all requests
 */

const { spawn } = require('child_process');
const readline = require('readline');

// Configuration
const REMOTE_HOST = process.env.MCP_SKYFI_HOST || 'your-aws-instance.com';
const REMOTE_USER = process.env.MCP_SKYFI_USER || 'ec2-user';
const API_KEY = process.env.SKYFI_API_KEY;

if (!API_KEY) {
  console.error('Error: SKYFI_API_KEY environment variable is required');
  process.exit(1);
}

// Launch SSH connection to remote MCP server
const mcp = spawn('ssh', [
  '-o', 'StrictHostKeyChecking=no',
  '-o', 'UserKnownHostsFile=/dev/null',
  `${REMOTE_USER}@${REMOTE_HOST}`,
  'cd /home/ec2-user/mcp-skyfi && source venv/bin/activate && python -m mcp_skyfi'
], {
  stdio: ['pipe', 'pipe', 'inherit']
});

// Handle process errors
mcp.on('error', (err) => {
  console.error('Failed to start MCP server:', err);
  process.exit(1);
});

mcp.on('exit', (code) => {
  process.exit(code);
});

// Create readline interface for parsing JSON lines
const rl = readline.createInterface({
  input: process.stdin,
  terminal: false
});

// Process incoming requests from Claude Desktop
rl.on('line', (line) => {
  try {
    const request = JSON.parse(line);
    
    // Inject API key into request metadata
    if (request.method) {
      request.metadata = request.metadata || {};
      request.metadata.headers = request.metadata.headers || {};
      request.metadata.headers['X-Skyfi-Api-Key'] = API_KEY;
      
      // Log for debugging (remove in production)
      if (process.env.DEBUG) {
        console.error('Injecting API key into request:', request.method);
      }
    }
    
    // Forward modified request to MCP server
    mcp.stdin.write(JSON.stringify(request) + '\n');
    
  } catch (err) {
    // Not JSON or parsing error, forward as-is
    mcp.stdin.write(line + '\n');
  }
});

// Forward responses from MCP server back to Claude Desktop
mcp.stdout.on('data', (data) => {
  process.stdout.write(data);
});

// Handle stdin close
rl.on('close', () => {
  mcp.stdin.end();
});

// Handle signals
process.on('SIGINT', () => {
  mcp.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  mcp.kill('SIGTERM');
  process.exit(0);
});