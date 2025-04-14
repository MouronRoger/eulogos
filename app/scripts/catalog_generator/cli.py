"""Command-line interface for the catalog generator."""

import argparse
import logging
from pathlib import Path

from app.scripts.catalog_generator.config import CatalogGeneratorConfig
from app.scripts.catalog_generator.catalog_builder import generate_catalog


def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        The parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate an integrated catalog of authors and works from XML files.'
    )
    parser.add_argument(
        '--data-dir', 
        default='data', 
        help='Path to the data directory (default: data)'
    )
    parser.add_argument(
        '--output',
        default='integrated_catalog.json',
        help='Output file path (default: integrated_catalog.json)',
    )
    parser.add_argument(
        '--author-index',
        default='author_index.json',
        help='Path to author_index.json file (default: author_index.json)',
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Enable verbose output'
    )
    parser.add_argument(
        '--stats-only', 
        action='store_true', 
        help='Only generate corpus statistics without texts'
    )
    parser.add_argument(
        '--include-content-sample', 
        action='store_true', 
        help='Include a small sample of text content in the catalog (first paragraph)'
    )
    
    return parser.parse_args()


def progress_reporter(progress: int, message: str):
    """Report progress to the console.
    
    Args:
        progress: Progress percentage (0-100)
        message: Progress message
    """
    print(f"[{progress:3d}%] {message}")


def main():
    """Main entry point for the command line interface."""
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = CatalogGeneratorConfig(
        data_dir=Path(args.data_dir),
        output_file=Path(args.output),
        author_index=Path(args.author_index),
        log_level="debug" if args.verbose else "info",
        stats_only=args.stats_only,
        include_content_sample=args.include_content_sample
    )
    
    # Generate the catalog
    generate_catalog(config, progress_reporter)


if __name__ == "__main__":
    main() 