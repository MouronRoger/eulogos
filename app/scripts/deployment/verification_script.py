#!/usr/bin/env python3
"""
Verification script for Eulogos deployments.

This script performs comprehensive verification of a deployment to ensure
it's functioning correctly before marking it as verified.
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.request
from typing import Dict, List, Tuple

# Import from the same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from deployment_tracker import DeploymentTracker  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("verification")


def check_health(url: str, timeout: int = 10) -> Tuple[bool, Dict]:
    """Check the health endpoint of the deployed application.

    Args:
        url: Health endpoint URL
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, response_data)
    """
    logger.info(f"Checking health endpoint: {url}")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                logger.error(f"Health check failed with status {response.status}")
                return False, {"error": f"Health check failed with status {response.status}"}

            data = json.loads(response.read().decode("utf-8"))
            logger.info(f"Health check successful. Response: {data}")
            return True, data
    except Exception as e:
        logger.error(f"Health check exception: {str(e)}")
        return False, {"error": f"Health check exception: {str(e)}"}


def check_version(health_data: Dict, expected_version: str) -> bool:
    """Verify the deployed version matches the expected version.

    Args:
        health_data: Health endpoint response data
        expected_version: Expected version string

    Returns:
        True if versions match, False otherwise
    """
    logger.info(f"Checking version. Expected: {expected_version}")
    if "version" not in health_data:
        logger.warning("Version information not found in health check response")
        return False

    if health_data["version"] != expected_version:
        logger.error(f"Version mismatch: Expected {expected_version}, got {health_data['version']}")
        return False

    logger.info("Version check passed")
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
    logger.info(f"Checking {len(endpoints)} API endpoints")
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"  Testing endpoint: {url}")
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                success = response.status == 200
                results[endpoint] = success
                if success:
                    logger.info(f"  ✓ Endpoint {endpoint} check passed (Status: {response.status})")
                else:
                    logger.error(f"  ✗ Endpoint {endpoint} check failed (Status: {response.status})")
        except Exception as e:
            logger.error(f"  ✗ Endpoint {endpoint} check failed with exception: {str(e)}")
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
    logger.info(f"Checking response times (threshold: {threshold_ms}ms)")
    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"  Testing response time for: {url}")
        try:
            start_time = time.time()
            with urllib.request.urlopen(url, timeout=5) as response:
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                within_threshold = response_time_ms <= threshold_ms

                results[endpoint] = {
                    "response_time_ms": response_time_ms,
                    "within_threshold": within_threshold,
                    "status": response.status,
                }

                if within_threshold:
                    logger.info(f"  ✓ Response time: {response_time_ms:.2f}ms (within threshold)")
                else:
                    logger.error(f"  ✗ Response time: {response_time_ms:.2f}ms (exceeds threshold of {threshold_ms}ms)")

        except Exception as e:
            logger.error(f"  ✗ Response time check failed for {endpoint}: {str(e)}")
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
    logger.info(f"Checking content for {len(pages)} pages")
    results = {}

    for page in pages:
        path = page["path"]
        expected_content = page["expected_content"]
        url = f"{base_url}{path}"

        logger.info(f"  Testing content for: {url}")
        logger.info(f"  Expected content: '{expected_content}'")

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode("utf-8")
                content_found = expected_content in content
                results[path] = content_found

                if content_found:
                    logger.info(f"  ✓ Expected content found on {path}")
                else:
                    logger.error(f"  ✗ Expected content NOT found on {path}")
                    # Add sample of actual content for debugging
                    if len(content) > 200:
                        logger.debug(f"  Content sample: '{content[:200]}...'")
                    else:
                        logger.debug(f"  Content: '{content}'")

        except Exception as e:
            logger.error(f"  ✗ Content check failed for {path}: {str(e)}")
            results[path] = False

    return results


def check_xml_functionality(base_url: str) -> bool:
    """Specifically check XML processing functionality.

    Since the branch name suggests this is related to XML processing,
    add specific checks for XML-related endpoints.

    Args:
        base_url: Base URL of the deployed application

    Returns:
        True if all XML checks pass, False otherwise
    """
    logger.info("Checking XML processing functionality")

    # Example URN for a known text
    test_urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

    # Test reader endpoint with the URN
    reader_url = f"{base_url}/read/{test_urn}"
    logger.info(f"  Testing XML reader: {reader_url}")

    try:
        with urllib.request.urlopen(reader_url, timeout=10) as response:
            content = response.read().decode("utf-8")
            if response.status != 200:
                logger.error(f"  ✗ XML reader check failed with status {response.status}")
                return False

            # Check for signs that XML is being processed correctly
            if "text-part" not in content or "content" not in content:
                logger.error("  ✗ XML reader doesn't show proper content structure")
                return False

            logger.info("  ✓ XML reader check passed")

            # Test reference navigation
            ref_url = f"{base_url}/api/references/{test_urn}"
            logger.info(f"  Testing XML references: {ref_url}")

            try:
                with urllib.request.urlopen(ref_url, timeout=10) as ref_response:
                    ref_content = ref_response.read().decode("utf-8")
                    if "href=" not in ref_content:
                        logger.error("  ✗ XML references don't contain navigation links")
                        return False

                    logger.info("  ✓ XML references check passed")
                    return True
            except Exception as e:
                logger.error(f"  ✗ XML references check failed: {str(e)}")
                return False

    except Exception as e:
        logger.error(f"  ✗ XML reader check failed: {str(e)}")
        return False


def run_verification(environment: str, deployment_id: str, verbose: bool = False) -> bool:
    """Run a comprehensive verification of the deployment.

    Args:
        environment: Deployment environment (staging or production)
        deployment_id: ID of the deployment to verify
        verbose: Enable verbose logging

    Returns:
        True if verification passed, False otherwise
    """
    # Set log level based on verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Log verification start
    logger.info(f"Starting verification for deployment ID: {deployment_id}")
    logger.info(f"Environment: {environment}")

    # Get the base URL for the environment
    if environment == "production":
        base_url = "https://eulogos.example.com"
    else:
        base_url = f"https://{environment}.eulogos.example.com"

    logger.info(f"Using base URL: {base_url}")

    # Track overall verification status
    verification_passed = True

    # Run health check
    logger.info(f"Checking health endpoint at {base_url}/health")
    health_success, health_data = check_health(f"{base_url}/health")

    if not health_success:
        logger.error(f"Health check failed: {health_data.get('error', 'Unknown error')}")
        verification_passed = False
    else:
        logger.info("✓ Health check passed")

    # Check key API endpoints
    logger.info("Checking API endpoints")
    api_endpoints = ["/api/browse", "/health/ready", "/health/live"]
    api_results = check_api_endpoints(base_url, api_endpoints)

    api_success = all(api_results.values())
    if not api_success:
        logger.error("API endpoint checks failed:")
        for endpoint, success in api_results.items():
            logger.error(f"  {endpoint}: {'✓ Success' if success else '✗ Failed'}")
        verification_passed = False
    else:
        logger.info("✓ API endpoint checks passed")

    # Check response times
    logger.info("Checking response times")
    perf_endpoints = ["/", "/api/browse", "/health"]
    perf_results = check_response_times(base_url, perf_endpoints)

    perf_success = all(result.get("within_threshold", False) for result in perf_results.values())
    if not perf_success:
        logger.error("Response time checks failed:")
        for endpoint, result in perf_results.items():
            if "error" in result:
                logger.error(f"  {endpoint}: ✗ Error - {result['error']}")
            else:
                logger.error(
                    f"  {endpoint}: {result['response_time_ms']:.2f}ms "
                    + f"({'✓ Within' if result['within_threshold'] else '✗ Exceeds'} threshold)"
                )
        verification_passed = False
    else:
        logger.info("✓ Response time checks passed")

    # Check for expected content
    logger.info("Checking page content")
    content_checks = [
        {"path": "/", "expected_content": "Eulogos"},
        {"path": "/api/browse", "expected_content": "author-works-tree"},
    ]
    content_results = check_content(base_url, content_checks)

    content_success = all(content_results.values())
    if not content_success:
        logger.error("Content checks failed:")
        for path, success in content_results.items():
            logger.error(f"  {path}: {'✓ Success' if success else '✗ Failed'}")
        verification_passed = False
    else:
        logger.info("✓ Content checks passed")

    # Since this is related to Branch-2_XML, specifically check XML functionality
    xml_success = check_xml_functionality(base_url)
    if not xml_success:
        logger.error("XML processing functionality checks failed")
        verification_passed = False
    else:
        logger.info("✓ XML processing functionality checks passed")

    # Final verification result
    if verification_passed:
        logger.info("✓ All verification checks passed!")
    else:
        logger.error("✗ Verification failed - one or more checks did not pass")

    return verification_passed


def main():
    """Parse command line arguments and run verification."""
    parser = argparse.ArgumentParser(description="Verify a deployment")
    parser.add_argument("--environment", "-e", required=True, help="Deployment environment")
    parser.add_argument("--deployment-id", "-d", required=True, help="Deployment ID to verify")
    parser.add_argument("--verified-by", "-u", default="verification-script", help="User who verified the deployment")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Run the verification
    success = run_verification(args.environment, args.deployment_id, args.verbose)

    if success:
        # Mark the deployment as verified
        tracker = DeploymentTracker()
        verify_success = tracker.mark_deployment_verified(args.deployment_id, args.verified_by)

        if verify_success:
            logger.info(f"Deployment {args.deployment_id} successfully verified")
            sys.exit(0)
        else:
            logger.error(f"Failed to mark deployment {args.deployment_id} as verified")
            sys.exit(1)
    else:
        # Mark the deployment as failed
        tracker = DeploymentTracker()
        tracker.mark_deployment_failed(args.deployment_id)

        logger.error(f"Deployment {args.deployment_id} verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
