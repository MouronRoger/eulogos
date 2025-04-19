"""Router for text reading operations.

This module provides enhanced endpoints for text reading functionality including:
- Text display with reference-based navigation
- Hierarchical reference extraction and browsing
- XML to HTML transformation with enhanced styling options
- Metadata exposure with rich context
- Token-level text processing
"""

from typing import Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response as TemplateResponse
from loguru import logger
from pathlib import Path as PathLib

from app.dependencies import get_catalog_service, get_xml_service
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService
from app.models.catalog import Author

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["reader"],
    responses={404: {"description": "Not found"}},
)


@router.get("/read/{text_id:path}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    text_id: str = Path(..., description="Text ID or path"),
    reference: Optional[str] = Query(None, description="Optional reference to navigate to"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Read a text with optional reference.

    Args:
        request: FastAPI request object
        text_id: Text ID or path
        reference: Optional reference to navigate to
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        HTMLResponse with rendered text
    """
    # First try to load as a direct path
    logger.debug(f"Reading text with ID/path: {text_id}, reference: {reference}")
    
    try:
        # Try loading directly as a path first
        xml_root = xml_service.load_xml_from_path(text_id)
        if xml_root is not None:
            logger.debug(f"Successfully loaded XML directly from path: {text_id}")
            # Get the HTML content
            try:
                html_content = xml_service._transform_element_to_html(xml_root, reference)
                if html_content is None:
                    logger.error(f"HTML content is None after transformation for path {text_id}")
                    html_content = "<div class='error'>Error: Failed to transform XML to HTML</div>"
                else:
                    logger.debug(f"Successfully transformed XML to HTML for path {text_id}, content length: {len(html_content)}")
            except Exception as transform_error:
                logger.exception(f"Error transforming XML to HTML for path {text_id}: {transform_error}")
                html_content = f"<div class='error'>Error transforming XML: {str(transform_error)}</div>"

            # Get adjacent references for navigation if a reference is provided
            try:
                adjacent_refs = xml_service.get_adjacent_references(xml_root, reference) if reference else {"prev": None, "next": None}
                logger.debug(f"Adjacent references for path {text_id}: prev={adjacent_refs['prev']}, next={adjacent_refs['next']}")
            except Exception as ref_error:
                logger.exception(f"Error getting adjacent references for path {text_id}: {ref_error}")
                adjacent_refs = {"prev": None, "next": None}

            # Create a minimal text object for the template
            text = {
                "id": text_id,
                "path": text_id,
                "group_name": "Unknown",
                "work_name": text_id,
                "language": "Unknown",
            }

            return templates.TemplateResponse(
                "reader.html",
                {
                    "request": request,
                    "text": text,
                    "author": None,
                    "content": html_content,
                    "reference": reference,
                    "prev_ref": adjacent_refs["prev"],
                    "next_ref": adjacent_refs["next"],
                    "path": text_id,
                },
            )
    except FileNotFoundError:
        # If loading as path fails, try as text ID
        pass
    except Exception as direct_load_error:
        logger.exception(f"Error loading directly from path {text_id}: {direct_load_error}")
        # Continue to try as text ID

    # If direct path loading failed, try as a text ID
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        logger.error(f"Text not found in catalog and not a valid path: {text_id}")
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            logger.error(f"No path found for text: {text_id}")
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        logger.debug(f"Found path for text {text_id}: {text.path}")
        
        # Ensure ID and path are synchronized
        if text.id != text.path:
            logger.warning(f"Text ID and path mismatch: id={text.id}, path={text.path}")
            # Update the ID to match the path
            text.id = text.path
        
        # Load and process the document
        try:
            xml_root = xml_service.load_xml_from_path(text.path)
            if xml_root is None:
                logger.error(f"XML root is None after loading from path: {text.path}")
                raise ValueError(f"Failed to load XML content from {text.path}")
            
            logger.debug(f"Successfully loaded XML for {text_id} from path: {text.path}")
        except Exception as xml_load_error:
            logger.exception(f"Error loading XML for text {text_id}: {xml_load_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error loading XML: {str(xml_load_error)}"
            )
        
        # Get the HTML content
        try:
            html_content = xml_service.transform_to_html(text_id, reference)
            if html_content is None:
                logger.error(f"HTML content is None after transformation for text {text_id}")
                html_content = "<div class='error'>Error: Failed to transform XML to HTML</div>"
            else:
                logger.debug(f"Successfully transformed XML to HTML for {text_id}, content length: {len(html_content)}")
        except Exception as transform_error:
            logger.exception(f"Error transforming XML to HTML for text {text_id}: {transform_error}")
            html_content = f"<div class='error'>Error transforming XML: {str(transform_error)}</div>"
        
        # Get adjacent references for navigation if a reference is provided
        try:
            adjacent_refs = xml_service.get_adjacent_references(xml_root, reference) if reference else {"prev": None, "next": None}
            logger.debug(f"Adjacent references for {text_id}: prev={adjacent_refs['prev']}, next={adjacent_refs['next']}")
        except Exception as ref_error:
            logger.exception(f"Error getting adjacent references for {text_id}: {ref_error}")
            adjacent_refs = {"prev": None, "next": None}

        # Get author if available
        author = None
        if text.author_id:
            authors = catalog_service.get_all_authors()
            for author_candidate in authors:
                # Handle both Author objects and dictionaries
                author_id = author_candidate.id if isinstance(author_candidate, Author) else author_candidate.get("id")
                if author_id == text.author_id:
                    # Convert dictionary to Author object if needed
                    if not isinstance(author_candidate, Author):
                        author = Author(
                            name=author_candidate.get("name", "Unknown"),
                            century=author_candidate.get("century", 0),
                            type=author_candidate.get("type", "unknown"),
                            id=author_candidate.get("id")
                        )
                    else:
                        author = author_candidate
                    break

        # Make sure HTML content is not None before rendering
        if html_content is None:
            logger.critical(f"HTML content is None right before template rendering for {text_id}")
            html_content = "<div class='error'>Critical error: HTML content is None</div>"

        # Render the template with the processed content
        logger.debug(f"Rendering template for {text_id}")
        return templates.TemplateResponse(
            request,
            "reader.html",
            {
                "text": text,
                "author": author,
                "content": html_content,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
                "path": text.path,  # Explicitly pass path to template
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing text {text_id}: {e}")
        
        # Add specific logging for NoneType has no len() error
        if "has no len()" in str(e):
            logger.debug(f"NoneType len() error detected for {text_id} - likely an issue with XML processing logic")
            detail = "Error: NoneType has no len() - This is a known issue we're fixing. Please try a different document."
        else:
            detail = f"Error processing text: {str(e)}"
            
        raise HTTPException(status_code=500, detail=detail)


@router.get("/document/{text_id}", response_class=JSONResponse)
async def get_document(
    text_id: str = Path(..., description="Text ID"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get document structure for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        JSONResponse with document structure
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Convert to a list of reference objects
        ref_list = []
        for ref, element in references.items():
            # Safely extract text content
            try:
                text_content = element.text or ""
                for child in element:
                    if child.tail:
                        text_content += child.tail
            except AttributeError:
                text_content = str(element)

            # Truncate if needed
            if len(text_content) > 100:
                text_content = text_content[:100] + "..."

            ref_list.append({
                "reference": ref,
                "text": text_content,
            })
        
        # Sort references
        ref_list.sort(key=lambda x: [int(n) if n.isdigit() else n for n in x["reference"].split(".")])
        
        return ref_list
    except Exception as e:
        logger.exception(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/passage/{text_id}/{reference}", response_class=HTMLResponse)
async def get_passage(
    request: Request,
    text_id: str = Path(..., description="Text ID"),
    reference: str = Path(..., description="Reference string"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get a specific passage from a text by reference.

    Args:
        request: FastAPI request object
        text_id: Text ID
        reference: Reference string
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        HTMLResponse with the specific passage
    """
    # Look up the text in the catalog
    logger.debug(f"Getting passage for text ID: {text_id}, reference: {reference}")
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        logger.error(f"Text not found: {text_id}")
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    # Get the actual content path
    if not text.path:
        logger.error(f"No path found for text: {text_id}")
        raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

    try:
        # Load and process the document
        try:
            xml_root = xml_service.load_xml_from_path(text.path)
            if xml_root is None:
                logger.error(f"XML root is None after loading from path: {text.path}")
                raise ValueError(f"Failed to load XML content from {text.path}")
                
            logger.debug(f"Successfully loaded XML for {text_id} from path: {text.path}")
        except Exception as xml_load_error:
            logger.exception(f"Error loading XML for text {text_id}: {xml_load_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error loading XML: {str(xml_load_error)}"
            )
        
        # Get the specific passage
        passage = xml_service.get_passage_by_reference(xml_root, reference)
        if not passage:
            logger.error(f"Reference not found: {reference} for text {text_id}")
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")
        
        logger.debug(f"Found passage for reference {reference} in text {text_id}")
        
        # Transform the passage to HTML
        try:
            html_content = xml_service._process_element_to_html(passage, reference)
            if html_content is None:
                logger.error(f"HTML content is None after processing passage for text {text_id}, reference {reference}")
                html_content = "<div class='error'>Error: Failed to process passage to HTML</div>"
            else:
                logger.debug(f"Successfully processed passage to HTML for {text_id}, reference {reference}, content length: {len(html_content)}")
        except Exception as transform_error:
            logger.exception(f"Error processing passage to HTML for text {text_id}, reference {reference}: {transform_error}")
            html_content = f"<div class='error'>Error processing passage: {str(transform_error)}</div>"
        
        # Get adjacent references for navigation
        try:
            adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
            logger.debug(f"Adjacent references for {text_id}, reference {reference}: prev={adjacent_refs['prev']}, next={adjacent_refs['next']}")
        except Exception as ref_error:
            logger.exception(f"Error getting adjacent references for {text_id}, reference {reference}: {ref_error}")
            adjacent_refs = {"prev": None, "next": None}
        
        # Render the passage template
        logger.debug(f"Rendering passage template for {text_id}, reference {reference}")
        return templates.TemplateResponse(
            request,
            "partials/passage.html",
            {
                "text": text,
                "content": html_content,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing passage for text {text_id}, reference {reference}: {e}")
        
        # Add specific logging for NoneType has no len() error
        if "has no len()" in str(e):
            logger.debug(f"NoneType len() error detected for passage {text_id}/{reference} - likely an issue with XML processing logic")
            detail = "Error: NoneType has no len() - This is a known issue we're fixing. Please try a different document or reference."
        else:
            detail = f"Error processing passage: {str(e)}"
            
        raise HTTPException(status_code=500, detail=detail)


@router.get("/references/{text_id}", response_class=JSONResponse)
async def get_references(
    text_id: str = Path(..., description="Text ID"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get all references for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        JSONResponse with all references
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Return just the list of reference strings
        return {"references": sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])}
    except Exception as e:
        logger.exception(f"Error processing references: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing references: {str(e)}")


@router.post("/texts/{text_id}/archive")
async def archive_text(
    text_id: str,
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Archive or unarchive a text.

    Args:
        text_id: Text ID
        archive: True to archive, False to unarchive
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success or failure
    """
    success = catalog_service.archive_text_by_id(text_id, archive)
    if not success:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    return {"success": True, "archived": archive}


@router.post("/texts/{text_id}/favorite")
async def favorite_text(
    text_id: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Toggle favorite status for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success and the new favorite status
    """
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    success = catalog_service.toggle_text_favorite_by_id(text_id)
    
    # Get the updated text to get the current favorite status
    text = catalog_service.get_text_by_id(text_id)
    
    return {"success": success, "favorite": text.favorite if text else False}


@router.get("/read/path/{path:path}", response_class=HTMLResponse)
async def read_text_by_path(
    request: Request,
    path: str = Path(..., description="File path relative to data directory"),
    reference: Optional[str] = Query(None, description="Optional reference to navigate to"),
    xml_service: XMLProcessorService = Depends(get_xml_service),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Read a text by its canonical path.

    Args:
        request: FastAPI request object
        path: File path relative to data directory
        reference: Optional reference to navigate to
        xml_service: XML service for processing text
        catalog_service: CatalogService instance

    Returns:
        HTMLResponse with rendered text
    """
    try:
        # Try to find the text metadata by path in the catalog
        text = None
        for t in catalog_service._texts_by_id.values():
            if t.path == path:
                text = t
                break
        
        # Load the document directly by path (no catalog lookup)
        xml_root = xml_service.load_xml_from_path(path)
        
        # Get the HTML content
        html_content = xml_service._process_element_to_html(xml_root)
        
        # Get adjacent references for navigation if a reference is provided
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference) if reference else {"prev": None, "next": None}
        
        # Get author if available and text was found
        author = None
        if text and text.author_id:
            author = catalog_service.get_author_by_id(text.author_id)
            
        # Render the template with the processed content
        return templates.TemplateResponse(
            request,
            "reader.html",
            {
                "text": text,
                "author": author,
                "content": html_content,
                "path": path,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
                "title": text.work_name if text else path, 
            },
        )
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except Exception as e:
        logger.exception(f"Error processing text at path {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.get("/references/path/{path:path}", response_class=JSONResponse)
async def get_references_by_path(
    path: str = Path(..., description="File path relative to data directory"),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get all references for a text by its canonical path.

    Args:
        path: File path relative to data directory
        xml_service: XML service for processing

    Returns:
        JSONResponse with all references
    """
    try:
        # Load and process the document directly by path
        xml_root = xml_service.load_xml_from_path(path)
        
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Return just the list of reference strings
        return {"references": sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])}
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except Exception as e:
        logger.exception(f"Error processing references: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing references: {str(e)}")


@router.get("/references/{path:path}", response_class=JSONResponse, include_in_schema=False)
async def get_references_by_path_no_prefix(
    path: str = Path(..., description="File path relative to data directory"),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Alternative route for getting references without the /api/v2 prefix."""
    logger.info(f"Handling non-prefixed reference request for path: {path}")
    
    # Remove .xml extension if present
    if path.endswith('.xml'):
        path = path[:-4]
    
    try:
        # Load and process the document directly by path
        xml_root = xml_service.load_xml_from_path(path + '.xml')
        if xml_root is None:
            logger.error(f"Failed to load XML for path: {path}")
            raise HTTPException(status_code=500, detail="Failed to load XML document")
            
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Return just the list of reference strings
        sorted_refs = sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])
        logger.info(f"Successfully processed references for path: {path}, found {len(sorted_refs)} references")
        return {"references": sorted_refs}
    except FileNotFoundError:
        logger.error(f"File not found in references endpoint: {path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except Exception as e:
        logger.exception(f"Error in get_references_by_path_no_prefix for path {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/passage/path/{path:path}/{reference}", response_class=HTMLResponse)
async def get_passage_by_path(
    request: Request,
    path: str = Path(..., description="File path relative to data directory"),
    reference: str = Path(..., description="Reference string"),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get a specific passage from a text by reference using canonical path.

    Args:
        request: FastAPI request object
        path: File path relative to data directory
        reference: Reference string
        xml_service: XML service for processing

    Returns:
        HTMLResponse with the specific passage
    """
    try:
        # Load and process the document directly by path
        xml_root = xml_service.load_xml_from_path(path)
        
        # Get the specific passage
        passage = xml_service.get_passage_by_reference(xml_root, reference)
        if not passage:
            logger.error(f"Reference not found: {reference}")
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")
        
        # Transform the passage to HTML
        html_content = xml_service._process_element_to_html(passage, reference)
        
        # Get adjacent references for navigation
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
        
        # Render the passage template
        return templates.TemplateResponse(
            request,
            "partials/passage.html",
            {
                "content": html_content,
                "path": path,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
            },
        )
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing passage: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing passage: {str(e)}")


@router.post("/texts/path/{path:path}/archive")
async def archive_text_by_path(
    path: str = Path(..., description="File path relative to data directory"),
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Archive or unarchive a text by its canonical path.

    Args:
        path: File path relative to data directory
        archive: True to archive, False to unarchive
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success or failure
    """
    # Find the text by path in the catalog
    text = None
    for t in catalog_service._texts_by_id.values():
        if t.path == path:
            text = t
            break
    
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found for path: {path}")
    
    success = catalog_service.archive_text_by_id(text.id, archive)
    return {"success": success, "archived": archive}


# Add alternative route for non-prefixed endpoint
@router.post("/texts/{path:path}/archive", include_in_schema=False)
async def archive_text_by_path_no_prefix(
    path: str = Path(..., description="File path relative to data directory"),
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Alternative route for archiving texts without the /api/v2 prefix."""
    return await archive_text_by_path(path, archive, catalog_service)


@router.post("/texts/path/{path:path}/favorite")
async def favorite_text_by_path(
    path: str = Path(..., description="File path relative to data directory"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Toggle favorite status for a text by its canonical path.

    Args:
        path: File path relative to data directory
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success and the new favorite status
    """
    # Find the text by path in the catalog
    text = None
    for t in catalog_service._texts_by_id.values():
        if t.path == path:
            text = t
            break
    
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found for path: {path}")
    
    success = catalog_service.toggle_text_favorite_by_id(text.id)
    
    # Get the updated text to get the current favorite status
    text = catalog_service.get_text_by_id(text.id)
    
    return {"success": success, "favorite": text.favorite if text else False}


# Add alternative route for non-prefixed endpoint
@router.post("/texts/{path:path}/favorite", include_in_schema=False)
async def favorite_text_by_path_no_prefix(
    path: str = Path(..., description="File path relative to data directory"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Alternative route for favoriting texts without the /api/v2 prefix."""
    return await favorite_text_by_path(path, catalog_service) 