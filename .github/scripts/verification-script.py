#!/usr/bin/env python3
"""
Verification script for Eulogos deployments.

This script performs comprehensive verification of a deployment to ensure
it's functioning correctly before marking it as verified.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Dict, List, Tuple


def check_health(url: str, timeout: int = 10) -> Tuple[bool, Dict]:
    """Check the health endpoint of the deployed application.

    Args:
        url: Health endpoint URL
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, response_data)
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return False, {"error": f"Health check failed with status {response.status}"}

            data = json.loads(response.read().decode("utf-8"))
            return True, data
    except Exception as e:
        return False, {"error": f"Health check exception: {str(e)}"}


def check_version(health_data: Dict, expected_version: str) -> bool:
    """Verify the deployed version matches the expected version.

    Args:
        health_data: Health endpoint response data
        expected_version: Expected version string

    Returns:
        True if versions match, False otherwise
    """
    if "version" not in health_data:
        print("Warning: Version information not found in health check response")
        return False

    if health_data["version"] != expected_version:
        print(f"Version mismatch: Expected {expected_version}, got {health_data['version']}")
        return False

    return True


def check_api_endpoints(base_url: str, endpoints: List[str], timeout: int = 10) -> Dict[str, bool]:
    """Verify that key API endpoints are responding.

    Args:
        base_url: Base URL of the deployed application
        endpoints: List of endpoints to check
        timeout: Request timeout in seconds

    Returns:
        Dictionary of endpoint to success status
    """
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                results[endpoint] = response.status == 200
        except Exception:
            results[endpoint] = False

    return results


def check_response_times(base_url: str, endpoints: List[str], threshold_ms: int = 500) -> Dict[str, Dict]:
    """Measure response times for critical endpoints.

    Args:
        base_url: Base URL of the deployed application
        endpoints: List of endpoints to check
        threshold_ms: Maximum acceptable response time in milliseconds

    Returns:
        Dictionary of endpoint to performance data
    """
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            start_time = time.time()
            with urllib.request.urlopen(url, timeout=5) as response:
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                results[endpoint] = {
                    "response_time_ms": response_time_ms,
                    "within_threshold": response_time_ms <= threshold_ms,
                    "status": response.status,
                }
        except Exception as e:
            results[endpoint] = {"error": str(e), "within_threshold": False}

    return results


def check_content(base_url: str, pages: List[Dict]) -> Dict[str, bool]:
    """Check that pages contain expected content.

    Args:
        base_url: Base URL of the deployed application
        pages: List of dictionaries with path and expected_content

    Returns:
        Dictionary of page path to content check result
    """
    results = {}

    for page in pages:
        path = page["path"]
        expected_content = page["expected_content"]
        url = f"{base_url}{path}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode("utf-8")
                results[path] = expected_content in content
        except Exception:
            results[path] = False

    return results


def run_verification(environment: str, deployment_id: str) -> bool:
    """Run a comprehensive verification of the deployment.

    Args:
        environment: Deployment environment (staging or production)
        deployment_id: ID of the deployment to verify

    Returns:
        True if verification passed, False otherwise
    """
    # Get the base URL for the environment
    if environment == "production":
        base_url = "https://eulogos.example.com"
    else:
        base_url = f"https://{environment}.eulogos.example.com"

    # Run health check
    print(f"Checking health endpoint at {base_url}/health")
    health_success, health_data = check_health(f"{base_url}/health")

    if not health_success:
        print(f"Health check failed: {health_data.get('error', 'Unknown error')}")
        return False

    print("Health check passed")

    # Check key API endpoints
    print("Checking API endpoints")
    api_endpoints = ["/api/browse", "/health/ready", "/health/live"]
    api_results = check_api_endpoints(base_url, api_endpoints)

    api_success = all(api_results.values())
    if not api_success:
        print("API endpoint checks failed:")
        for endpoint, success in api_results.items():
            print(f"  {endpoint}: {'Success' if success else 'Failed'}")
        return False

    print("API endpoint checks passed")

    # Check response times
    print("Checking response times")
    perf_endpoints = ["/", "/api/browse", "/health"]
    perf_results = check_response_times(base_url, perf_endpoints)

    perf_success = all(result.get("within_threshold", False) for result in perf_results.values())
    if not perf_success:
        print("Response time checks failed:")
        for endpoint, result in perf_results.items():
            if "error" in result:
                print(f"  {endpoint}: Error - {result['error']}")
            else:
                print(
                    f"  {endpoint}: {result['response_time_ms']:.2f}ms "
                    + f"({'Within' if result['within_threshold'] else 'Exceeds'} threshold)"
                )
        return False

    print("Response time checks passed")

    # Check for expected content
    print("Checking page content")
    content_checks = [
        {"path": "/", "expected_content": "Eulogos"},
        {"path": "/api/browse", "expected_content": "author-works-tree"},
    ]
    content_results = check_content(base_url, content_checks)

    content_success = all(content_results.values())
    if not content_success:
        print("Content checks failed:")
        for path, success in content_results.items():
            print(f"  {path}: {'Success' if success else 'Failed'}")
        return False

    print("Content checks passed")

    # All checks passed
    print("All verification checks passed!")
    return True


def main():
    """Parse command line arguments and run verification."""
    parser = argparse.ArgumentParser(description="Verify a deployment")
    parser.add_argument("--environment", "-e", required=True, help="Deployment environment")
    parser.add_argument("--deployment-id", "-d", required=True, help="Deployment ID to verify")
    parser.add_argument("--verified-by", "-u", default="verification-script", help="User who verified the deployment")

    args = parser.parse_args()

    # Ensure deployment_tracker is in the Python path and import it
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from deployment_tracker import DeploymentTracker

    # Run the verification
    success = run_verification(args.environment, args.deployment_id)

    if success:
        # Mark the deployment as verified
        tracker = DeploymentTracker()
        verify_success = tracker.mark_deployment_verified(args.deployment_id, args.verified_by)

        if verify_success:
            print(f"Deployment {args.deployment_id} successfully verified")
            sys.exit(0)
        else:
            print(f"Failed to mark deployment {args.deployment_id} as verified")
            sys.exit(1)
    else:
        # Mark the deployment as failed
        tracker = DeploymentTracker()
        tracker.mark_deployment_failed(args.deployment_id)

        print(f"Deployment {args.deployment_id} verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
