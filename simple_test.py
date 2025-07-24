#!/usr/bin/env python3
import sys
import json

# Simple test to see if Claude Desktop is calling the script
print(json.dumps({"message": "Server started", "args": sys.argv}), file=sys.stderr)

# Keep running
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        print(json.dumps({"received": line.strip()}), file=sys.stderr)
    except:
        break