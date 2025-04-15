#!/usr/bin/env python3
"""
Deployment Tracker for the Eulogos project.

This script manages a database of deployments, allowing flexible rollbacks
to any previously successful deployment from any branch.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional


class DeploymentTracker:
    """Track deployments across environments and branches."""

    def __init__(self, db_path: str = ".github/deployments.db"):
        """Initialize the deployment tracker.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Create the database and tables if they don't exist."""
        # Make sure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create the deployments table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS deployments (
            id TEXT PRIMARY KEY,
            environment TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            branch_name TEXT NOT NULL,
            image_tag TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            deployed_by TEXT NOT NULL,
            status TEXT NOT NULL,
            verified_timestamp TEXT,
            verified_by TEXT
        )
        """
        )

        # Create indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_environment ON deployments(environment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON deployments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_branch ON deployments(branch_name)")

        conn.commit()
        conn.close()

    def record_deployment(self, deployment_data: Dict) -> bool:
        """Record a new deployment.

        Args:
            deployment_data: Dictionary with deployment information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = [
                "id",
                "environment",
                "commit_sha",
                "branch_name",
                "image_tag",
                "timestamp",
                "deployed_by",
                "status",
            ]
            for field in required_fields:
                if field not in deployment_data:
                    print(f"Error: Missing required field '{field}'")
                    return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert the deployment record
            cursor.execute(
                """
            INSERT INTO deployments (
                id, environment, commit_sha, branch_name, image_tag,
                timestamp, deployed_by, status, verified_timestamp, verified_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    deployment_data["id"],
                    deployment_data["environment"],
                    deployment_data["commit_sha"],
                    deployment_data["branch_name"],
                    deployment_data["image_tag"],
                    deployment_data["timestamp"],
                    deployment_data["deployed_by"],
                    deployment_data["status"],
                    deployment_data.get("verified_timestamp"),
                    deployment_data.get("verified_by"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error recording deployment: {e}")
            return False

    def mark_deployment_verified(self, deployment_id: str, verified_by: str) -> bool:
        """Mark a deployment as verified.

        Args:
            deployment_id: ID of the deployment to mark as verified
            verified_by: User who verified the deployment

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update the deployment status
            verified_timestamp = datetime.utcnow().isoformat() + "Z"
            cursor.execute(
                """
            UPDATE deployments
            SET status = 'verified', verified_timestamp = ?, verified_by = ?
            WHERE id = ?
            """,
                (verified_timestamp, verified_by, deployment_id),
            )

            if cursor.rowcount == 0:
                print(f"Error: Deployment {deployment_id} not found")
                conn.close()
                return False

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error marking deployment as verified: {e}")
            return False

    def mark_deployment_failed(self, deployment_id: str) -> bool:
        """Mark a deployment as failed.

        Args:
            deployment_id: ID of the deployment to mark as failed

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update the deployment status
            cursor.execute(
                """
            UPDATE deployments
            SET status = 'failed'
            WHERE id = ?
            """,
                (deployment_id,),
            )

            if cursor.rowcount == 0:
                print(f"Error: Deployment {deployment_id} not found")
                conn.close()
                return False

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error marking deployment as failed: {e}")
            return False

    def get_deployment(self, deployment_id: str) -> Optional[Dict]:
        """Get a specific deployment.

        Args:
            deployment_id: ID of the deployment to get

        Returns:
            Deployment information as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT * FROM deployments
            WHERE id = ?
            """,
                (deployment_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)

            return None

        except Exception as e:
            print(f"Error getting deployment: {e}")
            return None

    def get_latest_verified_deployment(self, environment: str, branch_name: Optional[str] = None) -> Optional[Dict]:
        """Get the latest verified deployment for an environment.

        Args:
            environment: Environment to get the deployment for
            branch_name: Optional branch name to filter by

        Returns:
            Latest verified deployment as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if branch_name:
                cursor.execute(
                    """
                SELECT * FROM deployments
                WHERE environment = ? AND status = 'verified' AND branch_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                    (environment, branch_name),
                )
            else:
                cursor.execute(
                    """
                SELECT * FROM deployments
                WHERE environment = ? AND status = 'verified'
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                    (environment,),
                )

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)

            return None

        except Exception as e:
            print(f"Error getting latest verified deployment: {e}")
            return None

    def list_deployments(
        self,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        branch_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """List deployments with optional filtering.

        Args:
            environment: Optional environment to filter by
            status: Optional status to filter by
            branch_name: Optional branch name to filter by
            limit: Maximum number of deployments to return

        Returns:
            List of deployments as dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM deployments"
            conditions = []
            params = []

            if environment:
                conditions.append("environment = ?")
                params.append(environment)

            if status:
                conditions.append("status = ?")
                params.append(status)

            if branch_name:
                conditions.append("branch_name = ?")
                params.append(branch_name)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Error listing deployments: {e}")
            return []

    def delete_deployment(self, deployment_id: str) -> bool:
        """Delete a deployment.

        Args:
            deployment_id: ID of the deployment to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
            DELETE FROM deployments
            WHERE id = ?
            """,
                (deployment_id,),
            )

            if cursor.rowcount == 0:
                print(f"Error: Deployment {deployment_id} not found")
                conn.close()
                return False

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error deleting deployment: {e}")
            return False


def main():
    """Parse command line arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Deployment Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record a new deployment")
    record_parser.add_argument("--id", required=True, help="Deployment ID")
    record_parser.add_argument("--environment", required=True, help="Deployment environment")
    record_parser.add_argument("--commit", required=True, help="Commit SHA")
    record_parser.add_argument("--branch", required=True, help="Branch name")
    record_parser.add_argument("--image-tag", required=True, help="Docker image tag")
    record_parser.add_argument("--deployed-by", required=True, help="User who deployed")
    record_parser.add_argument("--status", default="deployed", help="Deployment status")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Mark a deployment as verified")
    verify_parser.add_argument("--id", required=True, help="Deployment ID to mark as verified")
    verify_parser.add_argument("--verified-by", required=True, help="User who verified the deployment")

    # Fail command
    fail_parser = subparsers.add_parser("fail", help="Mark a deployment as failed")
    fail_parser.add_argument("--id", required=True, help="Deployment ID to mark as failed")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific deployment")
    get_parser.add_argument("--id", required=True, help="Deployment ID to get")

    # Latest command
    latest_parser = subparsers.add_parser("latest", help="Get the latest verified deployment")
    latest_parser.add_argument("--environment", required=True, help="Environment to get deployment for")
    latest_parser.add_argument("--branch", help="Branch name to filter by")

    # List command
    list_parser = subparsers.add_parser("list", help="List deployments")
    list_parser.add_argument("--environment", help="Environment to filter by")
    list_parser.add_argument("--status", help="Status to filter by")
    list_parser.add_argument("--branch", help="Branch name to filter by")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of deployments to list")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a deployment")
    delete_parser.add_argument("--id", required=True, help="Deployment ID to delete")

    args = parser.parse_args()

    # Initialize the tracker
    tracker = DeploymentTracker()

    if args.command == "record":
        # Record a new deployment
        deployment_data = {
            "id": args.id,
            "environment": args.environment,
            "commit_sha": args.commit,
            "branch_name": args.branch,
            "image_tag": args.image_tag,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "deployed_by": args.deployed_by,
            "status": args.status,
        }

        success = tracker.record_deployment(deployment_data)
        if success:
            print(f"Deployment {args.id} recorded successfully")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == "verify":
        # Mark a deployment as verified
        success = tracker.mark_deployment_verified(args.id, args.verified_by)
        if success:
            print(f"Deployment {args.id} marked as verified")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == "fail":
        # Mark a deployment as failed
        success = tracker.mark_deployment_failed(args.id)
        if success:
            print(f"Deployment {args.id} marked as failed")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == "get":
        # Get a specific deployment
        deployment = tracker.get_deployment(args.id)
        if deployment:
            print(json.dumps(deployment, indent=2))
            sys.exit(0)
        else:
            print(f"Deployment {args.id} not found")
            sys.exit(1)

    elif args.command == "latest":
        # Get the latest verified deployment
        deployment = tracker.get_latest_verified_deployment(args.environment, args.branch)
        if deployment:
            print(json.dumps(deployment, indent=2))
            sys.exit(0)
        else:
            print(f"No verified deployments found for {args.environment}")
            sys.exit(1)

    elif args.command == "list":
        # List deployments
        deployments = tracker.list_deployments(args.environment, args.status, args.branch, args.limit)
        if deployments:
            print(json.dumps(deployments, indent=2))
            sys.exit(0)
        else:
            print("No deployments found")
            sys.exit(1)

    elif args.command == "delete":
        # Delete a deployment
        success = tracker.delete_deployment(args.id)
        if success:
            print(f"Deployment {args.id} deleted successfully")
            sys.exit(0)
        else:
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
