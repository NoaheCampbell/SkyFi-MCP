#!/usr/bin/env python3
"""Simple wrapper to run MCP server with environment variables."""
import os
import sys
import subprocess

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main function
from mcp_skyfi import main

if __name__ == "__main__":
    main()