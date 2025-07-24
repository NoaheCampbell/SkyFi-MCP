"""Main entry point for MCP SkyFi server."""
import os
import sys
import click


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"], case_sensitive=False),
    default="stdio",
    help="Transport method to use"
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind HTTP server to (only for HTTP transport)"
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind HTTP server to (only for HTTP transport)"
)
def main(transport: str, host: str, port: int):
    """Run the SkyFi MCP server."""
    if transport == "stdio":
        # Run STDIO server
        from .servers.main import run_server
        import asyncio
        asyncio.run(run_server())
    else:
        # Run HTTP server
        import uvicorn
        from .servers.http_server_simple import app
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()