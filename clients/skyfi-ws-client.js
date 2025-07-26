#!/usr/bin/env node

const WebSocket = require('ws');
const readline = require('readline');

// Get WebSocket URL from environment or use default
const WS_URL = process.env.SKYFI_WS_URL || 'wss://attempt1-copy.fly.dev';

// Create readline interface for stdin
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Connect to WebSocket server
const ws = new WebSocket(WS_URL);

ws.on('open', () => {
  console.error(`Connected to MCP server at ${WS_URL}`);
  
  // Forward stdin to WebSocket
  rl.on('line', (line) => {
    ws.send(line);
  });
  
  // Handle stdin close
  process.stdin.on('end', () => {
    ws.close();
  });
});

// Forward WebSocket messages to stdout
ws.on('message', (data) => {
  console.log(data.toString());
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error.message);
  process.exit(1);
});

ws.on('close', () => {
  console.error('Disconnected from MCP server');
  process.exit(0);
});