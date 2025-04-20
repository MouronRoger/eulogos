"""Run script for Eulogos application.

This script starts the Eulogos application using Uvicorn.
"""

import argparse
import os
import uvicorn


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Eulogos application")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind to"
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
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    return parser.parse_args()


def main():
    """Run the application."""
    args = parse_args()
    
    # Set environment variables
    if args.debug:
        os.environ["EULOGOS_DEBUG"] = "True"
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
