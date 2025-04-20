"""Deployment tracking functionality for the application.

This module provides utilities for tracking deployments and managing rollbacks.
"""
from typing import Optional, Dict
import json
import os
import sys
import argparse
from datetime import datetime


def track_deployment(
    deployment_id: str,
    commit_sha: str,
    branch_name: str,
    environment: str,
    triggered_by: str,
    timestamp: Optional[str] = None,
) -> Dict[str, str]:
    """Track a new deployment by recording its metadata.

    Args:
        deployment_id: Unique identifier for the deployment
        commit_sha: Git commit SHA of the deployment
        branch_name: Name of the branch being deployed
        environment: Target environment (staging/production)
        triggered_by: User or process that triggered the deployment
        timestamp: Optional timestamp of deployment, defaults to current time

    Returns:
        Dict containing the deployment metadata
    """
    if not timestamp:
        timestamp = datetime.utcnow().isoformat()

    deployment_data = {
        "id": deployment_id,
        "commit_sha": commit_sha,
        "branch_name": branch_name,
        "environment": environment,
        "triggered_by": triggered_by,
        "timestamp": timestamp,
    }

    # Ensure the deployments directory exists
    os.makedirs("logs/deployments", exist_ok=True)

    # Save deployment metadata
    deployment_file = f"logs/deployments/{deployment_id}.json"
    with open(deployment_file, "w") as f:
        json.dump(deployment_data, f, indent=2)

    return deployment_data


def get_latest_deployment(environment: str) -> Optional[Dict[str, str]]:
    """Get the metadata of the latest successful deployment for an environment.

    Args:
        environment: Target environment (staging/production)

    Returns:
        Dict containing the deployment metadata or None if no deployments found
    """
    deployments_dir = "logs/deployments"
    if not os.path.exists(deployments_dir):
        return None

    latest_deployment = None
    latest_timestamp = None

    for filename in os.listdir(deployments_dir):
        if not filename.endswith(".json"):
            continue

        with open(os.path.join(deployments_dir, filename)) as f:
            try:
                deployment_data = json.load(f)
                if deployment_data["environment"] != environment:
                    continue

                timestamp = datetime.fromisoformat(deployment_data["timestamp"])
                if not latest_timestamp or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_deployment = deployment_data
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return latest_deployment


def get_deployment(deployment_id: str) -> Optional[Dict[str, str]]:
    """Get deployment metadata by ID.

    Args:
        deployment_id: The ID of the deployment to retrieve

    Returns:
        Dict containing the deployment metadata or None if not found
    """
    deployment_file = f"logs/deployments/{deployment_id}.json"
    if not os.path.exists(deployment_file):
        return None

    try:
        with open(deployment_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def main() -> None:
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(description="Deployment tracking utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record a new deployment")
    record_parser.add_argument("--id", required=True, help="Deployment ID")
    record_parser.add_argument("--environment", required=True, help="Target environment")
    record_parser.add_argument("--commit", required=True, help="Commit SHA")
    record_parser.add_argument("--branch", required=True, help="Branch name")
    record_parser.add_argument("--deployed-by", required=True, help="Deployment trigger")
    record_parser.add_argument("--image-tag", required=True, help="Docker image tag")
    record_parser.add_argument("--status", required=True, help="Deployment status")

    # Latest command
    latest_parser = subparsers.add_parser(
        "latest", help="Get latest deployment for environment"
    )
    latest_parser.add_argument("--environment", required=True, help="Target environment")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get deployment by ID")
    get_parser.add_argument("--id", required=True, help="Deployment ID")

    args = parser.parse_args()

    if args.command == "record":
        deployment = track_deployment(
            deployment_id=args.id,
            commit_sha=args.commit,
            branch_name=args.branch,
            environment=args.environment,
            triggered_by=args.deployed_by,
        )
        print(json.dumps(deployment))
        sys.exit(0)

    elif args.command == "latest":
        deployment = get_latest_deployment(args.environment)
        if deployment:
            print(json.dumps(deployment))
            sys.exit(0)
        else:
            print(f"No deployments found for environment: {args.environment}")
            sys.exit(1)

    elif args.command == "get":
        deployment = get_deployment(args.id)
        if deployment:
            print(json.dumps(deployment))
            sys.exit(0)
        else:
            print(f"Deployment not found: {args.id}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 