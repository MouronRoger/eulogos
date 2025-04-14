"""Pydantic models for catalog data."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class Author(BaseModel):
    """Author model."""
    
    name: str
    century: int  # Negative for BCE, positive for CE
    type: str
    id: Optional[str] = None  # Author ID (typically the textgroup)


class Text(BaseModel):
    """Text model with author reference."""
    
    urn: str
    group_name: str
    work_name: str
    language: str
    wordcount: int
    scaife: Optional[str] = None
    author_id: Optional[str] = None
    archived: bool = False  # Flag for archived texts
    favorite: bool = False  # Flag for favorite texts
    
    # Derived fields (not stored in JSON)
    namespace: Optional[str] = Field(None, exclude=True)
    textgroup: Optional[str] = Field(None, exclude=True)
    work_id: Optional[str] = Field(None, exclude=True)
    version: Optional[str] = Field(None, exclude=True)
    
    @validator('urn')
    def parse_urn(cls, v, values):
        """Extract URN components."""
        try:
            parts = v.split(":")
            if len(parts) >= 4:
                namespace = parts[2]
                identifier = parts[3].split(":")[0]
                id_parts = identifier.split(".")
                
                if len(id_parts) >= 3:
                    textgroup = id_parts[0]
                    work_id = id_parts[1]
                    version = id_parts[2]
                    
                    values["namespace"] = namespace
                    values["textgroup"] = textgroup
                    values["work_id"] = work_id
                    values["version"] = version
        except Exception:
            # If parsing fails, just return the URN as is
            pass
        
        return v


class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""
    
    nodeCount: int = 0
    greekWords: int = 0
    latinWords: int = 0
    arabicwords: int = 0
    authorCount: int = 0
    textCount: int = 0


class UnifiedCatalog(BaseModel):
    """Unified catalog model combining author and text data."""
    
    statistics: CatalogStatistics
    authors: Dict[str, Author]
    catalog: List[Text] 