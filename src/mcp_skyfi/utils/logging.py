"""Logging configuration for MCP SkyFi server."""
import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)