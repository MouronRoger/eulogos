# Flexible Rollback Workflow for Eulogos

This document explains the flexible deployment and rollback workflow for the Eulogos project, designed to support rolling back to any previous successful deployment from any branch.

## Overview

This workflow is designed to:

1. Deploy from any branch to staging or production environments
2. Track all deployments with detailed metadata
3. Verify deployment success with automated tests
4. Support rolling back to any previous successful deployment
5. Allow both automatic and manual rollbacks

The system maintains a complete history of all deployments across all branches, giving you the flexibility to roll back to any point in the project's history, regardless of which branch it came from.

## How It Works

### Deployment Tracking

Every deployment records:

- **Deployment ID**: Unique identifier (based on branch, commit, and timestamp)
- **Environment**: Target environment (staging or production)
- **Branch**: Source branch (main, branch_1, branch_2, etc.)
- **Commit SHA**: Specific commit that was deployed
- **Image Tag**: Docker image tag used
- **Timestamp**: When the deployment occurred
- **Status**: Current status (deployed, verified, failed)
- **Verification**: Timestamp and user who verified the deployment

This information is stored in a database and can be queried when you need to roll back.

### Unique Image Tags

Each deployment creates a Docker image with a unique tag composed of:
```
{branch_name}_{short_commit_sha}_{timestamp}
```

This ensures that every deployment can be uniquely identified and restored if needed.

### Workflow Jobs

1. **Prepare**: Determines if this is a regular deployment or rollback
2. **Build**: Builds the Docker image for regular deployments
3. **Deploy**: Deploys the image or rolls back to a previous deployment
4. **Verify**: Validates the deployment with automated checks
5. **Automatic Rollback**: Triggers a rollback if verification fails

## Using the Workflow

### Regular Deployment

Regular deployments happen automatically when you push to any branch. You can also manually trigger a deployment:

1. Go to Actions → Deploy with Flexible Rollback → Run workflow
2. Select the branch to deploy from
3. Choose the target environment (staging or production)
4. Make sure "Perform rollback" is **not** checked
5. Click "Run workflow"

The workflow will build and deploy your code, then verify it's working correctly.

### Manual Rollback

To roll back to a previous deployment:

1. Go to Actions → Deploy with Flexible Rollback → Run workflow
2. Select any branch (it doesn't matter for rollbacks)
3. Choose the target environment (staging or production)
4. Check "Perform rollback to a previous deployment"
5. Optionally specify a deployment ID (leave empty to use the latest successful deployment)
6. Click "Run workflow"

### Automatic Rollback

If a deployment fails verification, the workflow automatically triggers a rollback to the latest successful deployment for that environment.

## Command Line Tools

The included deployment tracker script provides command line access to deployment history:

```bash
# List recent deployments
python .github/scripts/deployment_tracker.py list --environment staging

# Get the latest verified deployment
python .github/scripts/deployment_tracker.py latest --environment production

# Get information about a specific deployment
python .github/scripts/deployment_tracker.py get --id branch_1_abc1234_20230415123456
```

## Customization

You can further enhance this workflow by:

1. **Adding More Verification Tests**: Expand the verification job with additional tests specific to your application
2. **Integrating Notifications**: Add Slack, email, or other notifications for deployment events
3. **Enhancing Deployment Tracking**: Extend the tracker with additional metadata
4. **Adding Blue/Green Deployments**: Implement zero-downtime deployments and rollbacks

## Troubleshooting

### Common Issues

1. **Build Failures**: Check the build logs for errors in your code
2. **Deployment Failures**: Verify Kubernetes configuration and credentials
3. **Verification Failures**: Check application logs and verify endpoint responses
4. **Rollback Issues**: Ensure the target deployment exists and has a valid Docker image

### Viewing Deployment History

Access your deployment history through:

1. **GitHub Actions Artifacts**: Each workflow run uploads its deployment metadata
2. **Deployment Database**: The SQLite database at `.github/deployments.db` contains all records
3. **Command Line**: Use the deployment tracker script to query records

## Implementation Requirements

To fully implement this workflow, you'll need:

1. **GitHub Actions**: Enabled for your repository
2. **Docker Registry**: Access to GitHub Container Registry or another Docker registry
3. **Kubernetes**: A Kubernetes cluster for deployments (or adapt to your deployment platform)
4. **Database Storage**: For the deployment tracker (uses SQLite by default)

## Conclusion

This flexible rollback system gives you complete control over your deployment history, allowing you to deploy from any branch and roll back to any previous successful deployment as needed.
