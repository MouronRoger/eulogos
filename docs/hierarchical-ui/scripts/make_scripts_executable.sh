#!/bin/bash
# Script to make all shell scripts executable

# Make verification script executable
chmod +x ../implementation/code/shell/verify_impl.sh
echo "✓ Made verify_impl.sh executable"

# Make purge legacy script executable
chmod +x ../implementation/code/shell/purge_legacy.sh
echo "✓ Made purge_legacy.sh executable"

echo "All scripts are now executable!"
