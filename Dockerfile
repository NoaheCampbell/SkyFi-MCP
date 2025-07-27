FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy all local files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir git+https://github.com/modelcontextprotocol/python-sdk.git
RUN pip install --no-cache-dir httpx pydantic python-dotenv click fastapi uvicorn sse-starlette redis sqlalchemy boto3 shapely websockets
RUN pip install --no-cache-dir -e . --no-deps

# Expose WebSocket port
EXPOSE 8765

# Run the WebSocket bridge
CMD ["python", "ws_bridge_v2.py"]