#!/usr/bin/env python3
"""Run the test suite for the Eulogos application.

This script runs the test suite for the Eulogos application, focusing on:
1. ID-based path resolution
2. Data integrity
3. Service-level functionality
4. API endpoints

It's designed to be run from the command line with optional arguments to run
specific test groups or control test execution.
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Eulogos test suite")
    
    parser.add_argument(
        "--group",
        choices=["all", "unit", "integration", "data", "api"],
        default="all",
        help="Test group to run (default: all)",
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting",
    )
    
    parser.add_argument(
        "--xvs", "--exclude-vs",
        action="store_true",
        help="Exclude venv and site-packages from coverage",
        dest="exclude_venv_site",
    )
    
    return parser.parse_args()


def get_test_files(group: str) -> List[str]:
    """Get the test files for the specified group.
    
    Args:
        group: The test group to run
        
    Returns:
        A list of test file paths
    """
    if group == "all":
        return ["tests/"]
    
    if group == "unit":
        return [
            "tests/test_catalog_service.py",
            "tests/test_xml_processor_service.py",
            "tests/test_export_service.py",
            "tests/test_catalog_models.py",
        ]
    
    if group == "integration":
        return ["tests/test_integration.py"]
    
    if group == "data":
        return ["tests/test_data_integrity.py"]
    
    if group == "api":
        return ["tests/test_id_based_endpoints.py"]
    
    return []


def run_tests(
    files: List[str],
    verbose: bool = False,
    coverage: bool = False,
    exclude_venv_site: bool = False,
) -> int:
    """Run the tests for the specified files.
    
    Args:
        files: The test files to run
        verbose: Whether to show verbose output
        coverage: Whether to run with coverage reporting
        exclude_venv_site: Whether to exclude venv and site-packages from coverage
        
    Returns:
        The exit code from the test run
    """
    cmd = []
    
    if coverage:
        cmd = ["coverage", "run", "--source=app"]
        
        if exclude_venv_site:
            cmd.extend(["--omit=*/venv/*,*/site-packages/*"])
        
        cmd.append("-m")
        cmd.append("pytest")
    else:
        cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(files)
    
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if coverage:
        subprocess.run(["coverage", "report", "-m"])
    
    return result.returncode


def main() -> int:
    """Run the test suite.
    
    Returns:
        The exit code from the test run
    """
    args = parse_args()
    
    # Set up environment for tests
    os.environ["TESTING"] = "1"
    
    # Get test files
    test_files = get_test_files(args.group)
    if not test_files:
        print(f"No test files found for group: {args.group}")
        return 1
    
    # Run tests
    return run_tests(
        test_files,
        verbose=args.verbose,
        coverage=args.coverage,
        exclude_venv_site=args.exclude_venv_site,
    )


if __name__ == "__main__":
    sys.exit(main()) 