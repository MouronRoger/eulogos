#!/usr/bin/env python3
"""Entry point script for running the Eulogos application."""

import argparse
import os
import sys
import webbrowser
from pathlib import Path

import uvicorn
from loguru import logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run the Eulogos application")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host address to bind to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload on file changes"
    )
    parser.add_argument(
        "--no-browser", 
        action="store_true", 
        help="Don't open a browser window"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level"
    )
    
    return parser.parse_args()


def setup_logger(log_level: str) -> None:
    """Set up the logger with the specified log level.
    
    Args:
        log_level: The log level to use
    """
    log_levels = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
    }
    level = log_levels.get(log_level.lower(), "INFO")
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(sys.stderr, level=level)
    
    # Add file logger
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/eulogos.log", rotation="10 MB", level="DEBUG")


def main() -> None:
    """Run the Eulogos application."""
    args = parse_args()
    setup_logger(args.log_level)
    
    logger.info(f"Starting Eulogos application")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Reload: {args.reload}")
    
    # Open browser after a short delay
    if not args.no_browser:
        import threading
        import time
        
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://{args.host}:{args.port}")
        
        threading.Thread(target=open_browser).start()
    
    # Run the application
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


if __name__ == "__main__":
    main() 