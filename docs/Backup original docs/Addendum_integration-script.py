#!/usr/bin/env python3
"""
Setup script for the simplified Eulogos application.

This script preserves your existing canonical catalog builder and Docker setup
while creating a simplified application layer that uses file paths as IDs.
"""

import os
import shutil
import sys
from pathlib import Path


def create_directory(path):
    """Create directory if it doesn't exist."""
    path = Path(path)
    if not path.exists():
        print(f"Creating directory: {path}")
        path.mkdir(parents=True)
    return path


def copy_file(src, dest):
    """Copy a file and print status."""
    src = Path(src)
    dest = Path(dest)
    
    if not src.exists():
        print(f"ERROR: Source file does not exist: {src}")
        return False
    
    print(f"Copying {src} -> {dest}")
    shutil.copy2(src, dest)
    return True


def write_file(path, content):
    """Write content to a file."""
    path = Path(path)
    print(f"Writing file: {path}")
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def backup_existing_code():
    """Backup existing application code."""
    if Path("app/backup").exists():
        print("Backup directory already exists, skipping backup.")
        return
    
    # Create backup directory
    backup_dir = create_directory("app/backup")
    
    # Copy directories to backup
    for dir_name in ["routers", "services", "models", "templates"]:
        src_dir = Path(f"app/{dir_name}")
        if src_dir.exists():
            dest_dir = backup_dir / dir_name
            print(f"Backing up {src_dir} -> {dest_dir}")
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
    
    # Copy individual files
    for file_name in ["main.py", "config.py"]:
        src_file = Path(f"app/{file_name}")
        if src_file.exists():
            dest_file = backup_dir / file_name
            copy_file(src_file, dest_file)
    
    print("Backup completed.")


def setup_minimal_app():
    """Set up the minimal application structure."""
    # Create directories
    app_dir = create_directory("app")
    create_directory("app/models")
    create_directory("app/services")
    create_directory("app/templates")
    create_directory("app/templates/partials")
    create_directory("app/templates/errors")
    create_directory("app/static")
    create_directory("app/static/css")
    create_directory("app/static/js")
    
    # Create __init__.py files
    for dir_path in [
        "app",
        "app/models",
        "app/services",
    ]:
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            write_file(init_file, "")
    
    print("Minimal app structure created.")


def main():
    """Main setup function."""
    print("Setting up simplified Eulogos application...")
    
    # Check if canonical_catalog_builder.py exists
    if not Path("app/services/canonical_catalog_builder.py").exists():
        print("WARNING: Could not find canonical_catalog_builder.py in the expected location.")
        continue_anyway = input("Continue anyway? (y/n): ").lower()
        if continue_anyway != 'y':
            print("Setup aborted.")
            sys.exit(1)
    
    # Backup existing code
    backup_existing_code()
    
    # Set up minimal app structure
    setup_minimal_app()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Add the simplified code files to the app directory")
    print("2. Verify Docker compatibility")
    print("3. Run the application with: python run.py --reload --debug")


if __name__ == "__main__":
    main()
