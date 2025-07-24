#!/bin/bash
# Remote MCP execution via SSH

# Configuration
REMOTE_HOST="${MCP_REMOTE_HOST:-your-server.com}"
REMOTE_USER="${MCP_REMOTE_USER:-ubuntu}"
REMOTE_KEY="${MCP_REMOTE_KEY:-~/.ssh/id_rsa}"

# Execute MCP server on remote host via SSH
ssh -i "$REMOTE_KEY" "$REMOTE_USER@$REMOTE_HOST" \
    "cd /opt/mcp-skyfi && SKYFI_API_KEY='$SKYFI_API_KEY' python -m mcp_skyfi"