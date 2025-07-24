"""Simple HTTP server wrapper for MCP SkyFi."""
import os
import subprocess
import sys
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="SkyFi MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SkyFi MCP Server",
        "version": "0.1.0",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/sse")
async def handle_sse(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_skyfi_api_key: Optional[str] = Header(None, alias="X-Skyfi-Api-Key")
):
    """Handle SSE connection with authentication."""
    # Extract API key from headers
    api_key = None
    
    if x_skyfi_api_key:
        api_key = x_skyfi_api_key
    elif x_api_key:
        api_key = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]
    
    # Create environment for subprocess
    env = os.environ.copy()
    if api_key:
        env["SKYFI_API_KEY"] = api_key
        logger.info("API key provided via headers")
    else:
        logger.warning("No API key provided in headers")
    
    # Run the MCP server as a subprocess with SSE transport
    async def generate():
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m", "mcp",
            "run",
            sys.executable,
            "-m", "src.mcp_skyfi.servers.main",
            "--transport", "sse",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        try:
            async for line in process.stdout:
                yield line
        finally:
            process.terminate()
            await process.wait()
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)