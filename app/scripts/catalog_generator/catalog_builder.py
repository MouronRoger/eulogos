"""Catalog builder for generating the integrated catalog."""

import os
import json
import logging
from pathlib import Path
from collections import OrderedDict, defaultdict
from typing import Dict, Any, List, Optional, Callable

from app.scripts.catalog_generator.config import CatalogGeneratorConfig
from app.scripts.catalog_generator.author_processor import load_author_index, process_author_cts
from app.scripts.catalog_generator.text_processor import process_work_cts

# Configure logging
logger = logging.getLogger(__name__)


def generate_catalog(
    config: CatalogGeneratorConfig,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict[str, Any]:
    """Generate the integrated catalog.
    
    Args:
        config: Configuration options
        progress_callback: Optional callback for progress reporting
        
    Returns:
        The generated catalog
    """
    # Initialize the catalog structure
    catalog = {
        "statistics": {
            "authorCount": 0,
            "textCount": 0,
            "greekWords": 0,
            "latinWords": 0,
            "arabicwords": 0,
            "editions": 0,
            "translations": 0,
            "files": 0
        },
        "authors": OrderedDict()
    }
    
    # Report progress
    if progress_callback:
        progress_callback(0, "Loading author metadata")
    
    # Load author metadata
    author_metadata = load_author_index(str(config.author_index))
    
    # Track processing statistics
    total_xml_files = 0
    processed_cts_files = 0
    
    # Estimate the total number of directories to process
    total_dirs = sum(1 for _ in os.walk(config.data_dir))
    processed_dirs = 0
    
    # Report progress
    if progress_callback:
        progress_callback(5, f"Scanning data directory: {config.data_dir}")
    
    logger.info(f"Scanning data directory: {config.data_dir}")
    
    # First pass: Process author-level __cts__.xml files
    for root, dirs, files in os.walk(config.data_dir):
        processed_dirs += 1
        
        # Report progress (first pass: 5-40%)
        if progress_callback and total_dirs > 0:
            progress = 5 + int((processed_dirs / total_dirs) * 35)
            progress_callback(progress, f"Processing author directories: {processed_dirs}/{total_dirs}")
        
        # Check if this is an author directory with a __cts__.xml file
        if "__cts__.xml" in files:
            author_cts_path = os.path.join(root, "__cts__.xml")
            
            # Get the author ID from the path
            path_parts = Path(root).parts
            if len(path_parts) < 2:  # Must have at least data_dir/author_id
                continue
                
            author_id = path_parts[-1]  # Last part of the path is author_id
            
            try:
                logger.info(f"Processing author: {author_cts_path}")
                
                # Get author metadata from author_index.json
                author_info = author_metadata.get(author_id, {})
                
                # Process the author CTS file
                process_author_cts(author_cts_path, catalog, author_id, author_info)
                
                processed_cts_files += 1
            except Exception as e:
                logger.error(f"Error processing author {author_cts_path}: {e}")
    
    # Reset for second pass
    processed_dirs = 0
    
    # Report progress
    if progress_callback:
        progress_callback(40, "Processing work directories")
    
    # Second pass: Process work-level __cts__.xml files and actual text files
    for root, dirs, files in os.walk(config.data_dir):
        processed_dirs += 1
        
        # Report progress (second pass: 40-90%)
        if progress_callback and total_dirs > 0:
            progress = 40 + int((processed_dirs / total_dirs) * 50)
            progress_callback(progress, f"Processing work directories: {processed_dirs}/{total_dirs}")
        
        # Skip processing if no XML files in this directory
        xml_files = [f for f in files if f.endswith('.xml') and f != '__cts__.xml']
        total_xml_files += len(xml_files)
        
        if "__cts__.xml" in files and len(xml_files) > 0:
            work_cts_path = os.path.join(root, "__cts__.xml")
            
            # Extract path components to identify author and work
            path_parts = Path(root).parts
            if len(path_parts) < 3:  # Must have at least data_dir/author_id/work_id
                continue
                
            author_id = path_parts[-2]  # Second-to-last part is author_id
            work_id = path_parts[-1]    # Last part is work_id
            
            # Skip if author not in catalog
            if author_id not in catalog["authors"]:
                continue
                
            try:
                logger.info(f"Processing work: {work_cts_path}")
                
                # Process the work CTS file
                process_work_cts(
                    work_cts_path, 
                    xml_files, 
                    root, 
                    catalog, 
                    author_id, 
                    work_id,
                    str(config.data_dir),
                    config.include_content_sample
                )
                
                processed_cts_files += 1
            except Exception as e:
                logger.error(f"Error processing work {work_cts_path}: {e}")
    
    # Report progress
    if progress_callback:
        progress_callback(90, "Finalizing catalog")
    
    # Sort authors alphabetically by name
    catalog["authors"] = OrderedDict(
        sorted(catalog["authors"].items(), key=lambda x: x[1].get("name", ""))
    )
    
    # Sort each author's works and their editions
    for author_id, author_data in catalog["authors"].items():
        # Sort works
        if "works" in author_data:
            author_data["works"] = OrderedDict(
                sorted(author_data["works"].items(), key=lambda x: x[1].get("title", ""))
            )
            
            # For each work, sort editions and translations
            for work_id, work_data in author_data["works"].items():
                # Create ordered pairs of editions and translations
                ordered_editions = []
                ordered_translations = []
                
                # Collect all editions and translations
                editions = work_data.get("editions", {})
                translations = work_data.get("translations", {})
                
                # Group editions and translations by language pairs
                language_pairs = defaultdict(list)
                
                # First, add all editions to their respective language buckets
                for edition_id, edition in editions.items():
                    lang = edition.get("lang", "unknown")
                    language_pairs[lang].append(("edition", edition_id, edition))
                
                # Then, try to match translations to their original language editions
                for trans_id, translation in translations.items():
                    lang = translation.get("lang", "unknown")
                    # If we have an edition in a language this was translated from, link them
                    found_match = False
                    for edition_lang in language_pairs:
                        if edition_lang != lang:
                            language_pairs[edition_lang].append(("translation", trans_id, translation))
                            found_match = True
                            break
                    
                    # If no match found, create a new entry
                    if not found_match:
                        language_pairs[lang].append(("translation", trans_id, translation))
                
                # Sort by language
                sorted_languages = sorted(language_pairs.keys())
                
                # Recreate editions and translations as ordered dicts
                ordered_editions_dict = OrderedDict()
                ordered_translations_dict = OrderedDict()
                
                # Process each language group
                for lang in sorted_languages:
                    # Sort items within a language group (editions first, then translations)
                    items = sorted(language_pairs[lang], key=lambda x: (0 if x[0] == "edition" else 1, x[1]))
                    
                    # Add to appropriate dictionary
                    for item_type, item_id, item_data in items:
                        if item_type == "edition":
                            ordered_editions_dict[item_id] = item_data
                        else:
                            ordered_translations_dict[item_id] = item_data
                
                # Update the work data with ordered editions and translations
                work_data["editions"] = ordered_editions_dict
                work_data["translations"] = ordered_translations_dict
    
    # Update statistics
    catalog["statistics"]["authorCount"] = len(catalog["authors"])
    catalog["statistics"]["textCount"] = sum(len(author_data.get("works", {})) 
                                          for author_data in catalog["authors"].values())
    catalog["statistics"]["files"] = total_xml_files
    
    # Report progress
    if progress_callback:
        progress_callback(95, "Writing catalog to file")
    
    # Write the catalog to the output file
    simplified = simplified_catalog(catalog) if config.stats_only else catalog
    
    with open(config.output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)
    
    # Log completion
    logger.info(f"Generated integrated catalog saved to {config.output_file}")
    logger.info(f"Statistics: {catalog['statistics']['authorCount']} authors, "
                f"{catalog['statistics']['textCount']} works, "
                f"{catalog['statistics']['editions']} editions, "
                f"{catalog['statistics']['translations']} translations")
    
    # Report completion
    if progress_callback:
        progress_callback(100, "Catalog generation complete")
    
    return catalog


def simplified_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simplified version of the catalog with only statistics.
    
    Args:
        catalog: The full catalog
        
    Returns:
        Simplified catalog with only statistics
    """
    return {
        "statistics": catalog["statistics"],
        "authorCount": catalog["statistics"]["authorCount"],
        "textCount": catalog["statistics"]["textCount"],
        "editionCount": catalog["statistics"]["editions"],
        "translationCount": catalog["statistics"]["translations"]
    } 