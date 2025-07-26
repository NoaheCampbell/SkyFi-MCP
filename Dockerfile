FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone your repo
RUN git clone https://github.com/NoaheCampbell/SkyFi-MCP.git .

# Install Python dependencies
RUN pip install --no-cache-dir git+https://github.com/modelcontextprotocol/python-sdk.git
RUN pip install --no-cache-dir httpx pydantic python-dotenv click fastapi uvicorn sse-starlette redis sqlalchemy boto3 shapely websockets
RUN pip install --no-cache-dir -e . --no-deps

# Copy the WebSocket bridge
COPY ws_bridge.py .

# Expose WebSocket port
EXPOSE 8080

# Run the WebSocket bridge
CMD ["python", "ws_bridge.py"]