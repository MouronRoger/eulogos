"""Service for catalog operations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from app.models.catalog import Author, Text, UnifiedCatalog


class CatalogService:
    """Service for accessing the unified catalog."""
    
    def __init__(self, catalog_path: str = None, author_path: str = None, data_dir: str = None):
        """Initialize the catalog service.
        
        Args:
            catalog_path: Path to the catalog_index.json file
            author_path: Path to the author_index.json file
            data_dir: Path to the data directory containing the XML files
        """
        self.catalog_path = Path(catalog_path) if catalog_path else Path("catalog_index.json")
        self.author_path = Path(author_path) if author_path else Path("author_index.json")
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        
        # Primary data
        self._catalog_data = None
        self._author_data = None
        self._unified_catalog = None
        
        # Derived indexes
        self._texts_by_urn: Dict[str, Text] = {}
        self._texts_by_author: Dict[str, List[Text]] = {}
        self._texts_by_language: Dict[str, List[Text]] = {}
        self._authors_by_century: Dict[int, List[Author]] = {}
        self._authors_by_type: Dict[str, List[Author]] = {}
        self._available_languages: Set[str] = set()
    
    def load_catalog(self) -> Dict:
        """Load the catalog data from file.
        
        Returns:
            The catalog data as a dictionary
        """
        if not self.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")
        
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self._catalog_data = json.load(f)
                logger.info(f"Loaded catalog from {self.catalog_path}")
                return self._catalog_data
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise
    
    def _save_catalog(self) -> bool:
        """Save the catalog data to file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._catalog_data:
            logger.error("No catalog data to save")
            return False
            
        try:
            # Update catalog entries with current state
            for text in self._texts_by_urn.values():
                # Find the corresponding entry in the catalog data
                for entry in self._catalog_data.get("catalog", []):
                    if entry.get("urn") == text.urn:
                        # Update with current state of archived/favorite
                        entry["archived"] = text.archived
                        entry["favorite"] = text.favorite
                        break
            
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(self._catalog_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved catalog to {self.catalog_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
            return False
    
    def load_authors(self) -> Dict:
        """Load the author data from file.
        
        Returns:
            The author data as a dictionary
        """
        if not self.author_path.exists():
            logger.error(f"Author file not found: {self.author_path}")
            raise FileNotFoundError(f"Author file not found: {self.author_path}")
        
        try:
            with open(self.author_path, "r", encoding="utf-8") as f:
                self._author_data = json.load(f)
                logger.info(f"Loaded authors from {self.author_path}")
                return self._author_data
        except Exception as e:
            logger.error(f"Error loading authors: {e}")
            raise
    
    def create_unified_catalog(self) -> UnifiedCatalog:
        """Create a unified catalog from the catalog and author data.
        
        Returns:
            A UnifiedCatalog object
        """
        if self._catalog_data is None:
            self.load_catalog()
        
        if self._author_data is None:
            self.load_authors()
        
        # Extract statistics
        stats = {
            "nodeCount": self._catalog_data.get("nodeCount", 0),
            "greekWords": self._catalog_data.get("greekWords", 0),
            "latinWords": self._catalog_data.get("latinWords", 0),
            "arabicwords": self._catalog_data.get("arabicwords", 0),
            "authorCount": len(self._author_data),
            "textCount": len(self._catalog_data.get("catalog", [])),
        }
        
        # Process catalog entries and link to authors
        catalog_entries = []
        for item in self._catalog_data.get("catalog", []):
            # Extract textgroup from URN
            textgroup = None
            try:
                urn_parts = item["urn"].split(":")
                if len(urn_parts) >= 4:
                    identifier = urn_parts[3].split(":")[0]
                    id_parts = identifier.split(".")
                    if len(id_parts) >= 1:
                        textgroup = id_parts[0]
            except Exception:
                pass
            
            # Add author_id reference if it exists in authors
            catalog_entry = item.copy()
            if textgroup and textgroup in self._author_data:
                catalog_entry["author_id"] = textgroup
            
            catalog_entries.append(Text(**catalog_entry))
        
        # Convert authors to model
        authors = {author_id: Author(**data) for author_id, data in self._author_data.items()}
        
        # Create unified catalog
        self._unified_catalog = UnifiedCatalog(
            statistics=stats,
            authors=authors,
            catalog=catalog_entries,
        )
        
        # Build indexes for efficient access
        self._build_indexes()
        
        logger.info(f"Created unified catalog with {len(authors)} authors and {len(catalog_entries)} texts")
        return self._unified_catalog
    
    def _build_indexes(self):
        """Build internal indexes for efficient access."""
        if not self._unified_catalog:
            logger.error("Cannot build indexes: unified catalog not created")
            return
            
        # Index texts by URN
        self._texts_by_urn = {text.urn: text for text in self._unified_catalog.catalog}
        
        # Index texts by author
        self._texts_by_author = {}
        for text in self._unified_catalog.catalog:
            if text.author_id:
                if text.author_id not in self._texts_by_author:
                    self._texts_by_author[text.author_id] = []
                self._texts_by_author[text.author_id].append(text)
        
        # Index texts by language
        self._texts_by_language = {}
        for text in self._unified_catalog.catalog:
            if text.language not in self._texts_by_language:
                self._texts_by_language[text.language] = []
            self._texts_by_language[text.language].append(text)
            self._available_languages.add(text.language)
        
        # Index authors by century and type
        self._authors_by_century = {}
        self._authors_by_type = {}
        
        for author_id, author in self._unified_catalog.authors.items():
            # Index by century
            if author.century not in self._authors_by_century:
                self._authors_by_century[author.century] = []
            self._authors_by_century[author.century].append(author)
            
            # Index by type
            if author.type not in self._authors_by_type:
                self._authors_by_type[author.type] = []
            self._authors_by_type[author.type].append(author)
    
    def get_text_by_urn(self, urn: str) -> Optional[Text]:
        """Get a text by its URN.
        
        Args:
            urn: The URN of the text
            
        Returns:
            The text object or None if not found
        """
        return self._texts_by_urn.get(urn)
    
    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Text]:
        """Get all texts by an author.
        
        Args:
            author_id: The ID of the author
            include_archived: Whether to include archived texts
            
        Returns:
            A list of text objects
        """
        texts = self._texts_by_author.get(author_id, [])
        if not include_archived:
            texts = [text for text in texts if not text.archived]
        return texts
    
    def get_all_authors(self, include_archived: bool = False) -> List[Author]:
        """Get all authors.
        
        Args:
            include_archived: Whether to include authors with only archived texts
            
        Returns:
            A list of author objects
        """
        if not self._unified_catalog:
            return []
            
        if include_archived:
            return list(self._unified_catalog.authors.values())
        
        # Filter out authors who have only archived texts
        result = []
        for author_id, author in self._unified_catalog.authors.items():
            texts = self.get_texts_by_author(author_id, include_archived=False)
            if texts:  # Author has at least one non-archived text
                result.append(author)
        
        return result
    
    def archive_text(self, urn: str, archive: bool = True) -> bool:
        """Archive or unarchive a text.
        
        Args:
            urn: The URN of the text
            archive: True to archive, False to unarchive
            
        Returns:
            True if successful, False if the text was not found
        """
        if urn not in self._texts_by_urn:
            return False
            
        text = self._texts_by_urn[urn]
        text.archived = archive
        self._save_catalog()
        return True
    
    def toggle_text_favorite(self, urn: str) -> bool:
        """Toggle favorite status for a text.
        
        Args:
            urn: The URN of the text
            
        Returns:
            True if successful, False if the text was not found
        """
        if urn not in self._texts_by_urn:
            return False
            
        text = self._texts_by_urn[urn]
        text.favorite = not text.favorite
        self._save_catalog()
        return True
    
    def delete_text(self, urn: str) -> bool:
        """Delete a text from the catalog.
        
        Args:
            urn: The URN of the text
            
        Returns:
            True if successful, False if the text was not found
        """
        if urn not in self._texts_by_urn:
            return False
            
        # Remove from catalog data
        if self._catalog_data and "catalog" in self._catalog_data:
            self._catalog_data["catalog"] = [
                entry for entry in self._catalog_data["catalog"]
                if entry.get("urn") != urn
            ]
        
        # Remove from unified catalog
        if self._unified_catalog:
            self._unified_catalog.catalog = [
                text for text in self._unified_catalog.catalog
                if text.urn != urn
            ]
        
        # Remove from indexes
        text = self._texts_by_urn.pop(urn, None)
        
        if text and text.author_id:
            if text.author_id in self._texts_by_author:
                self._texts_by_author[text.author_id] = [
                    t for t in self._texts_by_author[text.author_id]
                    if t.urn != urn
                ]
        
        if text and text.language:
            if text.language in self._texts_by_language:
                self._texts_by_language[text.language] = [
                    t for t in self._texts_by_language[text.language]
                    if t.urn != urn
                ]
        
        # Save changes
        self._save_catalog()
        return True
    
    def validate_catalog_files(self) -> Dict:
        """Validate synchronization between catalog data and files.
        
        Returns:
            Dictionary with validation results
        """
        if self._catalog_data is None:
            self.load_catalog()
        
        if self._author_data is None:
            self.load_authors()
        
        # Statistics
        stats = {
            "total_catalog_entries": len(self._catalog_data.get("catalog", [])),
            "total_authors": len(self._author_data),
            "missing_files": 0,
            "missing_authors": 0,
            "unlisted_files": 0
        }
        
        # Track issues
        missing_files = []
        missing_authors = []
        textgroups_without_authors = set()
        
        # Check each catalog entry for corresponding file
        for entry in self._catalog_data.get("catalog", []):
            urn = entry.get("urn", "")
            if not urn:
                continue
            
            # Parse URN
            try:
                parts = urn.split(":")
                if len(parts) >= 4:
                    namespace = parts[2]
                    identifier = parts[3].split(":")[0]
                    id_parts = identifier.split(".")
                    
                    if len(id_parts) >= 3:
                        textgroup = id_parts[0]
                        work = id_parts[1]
                        version = id_parts[2]
                        
                        # Check if author exists
                        if textgroup not in self._author_data:
                            textgroups_without_authors.add(textgroup)
                        
                        # Construct expected file path
                        file_path = self.data_dir / namespace / textgroup / work / f"{textgroup}.{work}.{version}.xml"
                        
                        # Check if file exists
                        if not file_path.exists():
                            missing_files.append((urn, str(file_path)))
            except Exception as e:
                logger.error(f"Error parsing URN {urn}: {e}")
        
        # Check for unlisted files
        all_xml_files = list(self.data_dir.glob("**/*.xml"))
        known_urns = [entry.get("urn", "") for entry in self._catalog_data.get("catalog", [])]
        
        for xml_file in all_xml_files:
            # Try to derive URN from file path
            try:
                relative_path = xml_file.relative_to(self.data_dir)
                parts = list(relative_path.parts)
                
                if len(parts) >= 4 and parts[3].endswith(".xml"):
                    file_name = parts[3].replace(".xml", "")
                    name_parts = file_name.split(".")
                    
                    if len(name_parts) >= 3:
                        textgroup = name_parts[0]
                        work = name_parts[1]
                        version = name_parts[2]
                        namespace = parts[0]
                        
                        # Construct URN
                        urn = f"urn:cts:{namespace}:{textgroup}.{work}.{version}"
                        
                        # Check if in catalog
                        if urn not in known_urns and not any(known_urn.startswith(urn + ":") for known_urn in known_urns):
                            # This file is not in the catalog
                            stats["unlisted_files"] += 1
            except Exception as e:
                logger.error(f"Error processing file {xml_file}: {e}")
        
        # Update statistics
        stats["missing_files"] = len(missing_files)
        stats["missing_authors"] = len(textgroups_without_authors)
        
        # Return validation results
        return {
            "stats": stats,
            "missing_files": missing_files,
            "textgroups_without_authors": list(textgroups_without_authors),
            "validity": stats["missing_files"] == 0 and stats["missing_authors"] == 0
        } 