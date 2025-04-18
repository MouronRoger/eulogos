"""Run script for Eulogos API.

This script serves the Eulogos API using uvicorn.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file if it exists
load_dotenv()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Eulogos API")
    parser.add_argument(
        "--host", default=os.getenv("EULOGOS_HOST", "127.0.0.1"), help="Host to listen on (default: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=int(os.getenv("EULOGOS_PORT", "8000")), help="Port to listen on")
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("EULOGOS_WORKERS", "1")),
        help="Number of worker processes",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("EULOGOS_RELOAD", "").lower() == "true",
        help="Enable auto-reload on code changes",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default=os.getenv("EULOGOS_LOG_LEVEL", "info").lower(),
        help="Log level",
    )
    return parser.parse_args()


def configure_logging(log_level):
    """Configure logging."""
    # Remove default loguru handler
    logger.remove()

    # Add handler for stderr with specified log level
    logger.add(sys.stderr, level=log_level.upper())

    # Add handler for file
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    logger.add(logs_dir / "eulogos.log", rotation="10 MB", level=log_level.upper())


def main():
    """Run the Eulogos API server."""
    args = parse_args()

    # Configure logging
    configure_logging(args.log_level)

    logger.info("Starting Eulogos application")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Reload: {args.reload}")

    # Import here to avoid circular imports
    import uvicorn

    # Run the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
