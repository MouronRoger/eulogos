#!/usr/bin/env python3
"""Entry point for Eulogos application.

This script starts the Eulogos application using Uvicorn.
"""

import argparse
import os
import uvicorn
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Eulogos application.")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    return parser.parse_args()


def write_pid_file() -> None:
    """Write the process ID to a file."""
    pid_file = Path("app.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))
    print(f"PID {os.getpid()} written to {pid_file}")


def main() -> None:
    """Run the application."""
    args = parse_arguments()
    
    # Write PID to file for easier process management
    write_pid_file()
    
    # Start the application
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
