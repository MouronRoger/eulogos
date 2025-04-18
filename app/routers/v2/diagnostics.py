"""Diagnostic endpoints for troubleshooting."""

import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService


# Simple direct URN to path function
def direct_urn_to_path(urn: str, data_path: str = "data") -> str:
    """Transform a URN directly to a file path.

    Examples:
        urn:cts:greekLit:tlg0532.tlg001.perseus-grc2 -> data/tlg0532/tlg001/tlg0532.tlg001.perseus-grc2.xml

    Returns:
        The file path corresponding to the URN
    """
    parts = urn.split(":")
    if len(parts) < 4:
        return f"Invalid URN format: {urn}"

    # Get the identifier (e.g., tlg0532.tlg001.perseus-grc2)
    identifier = parts[3].split("#")[0]

    # Split into components
    id_parts = identifier.split(".")
    if len(id_parts) < 3:
        return f"URN missing version information: {urn}"

    # Extract components
    textgroup = id_parts[0]
    work = id_parts[1]
    version = id_parts[2]

    # Construct the path
    path = f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"

    return path


# Create router
router = APIRouter(
    prefix="/debug",
    tags=["diagnostics"],
    responses={404: {"description": "Not found"}},
)


@router.get("/path/{urn}", response_model=None)
async def debug_path_resolution(
    urn: str,
    data_path: str = Query("data", description="Base path for data files"),
    check_alternates: bool = Query(True, description="Check alternate path formats"),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Debug URN to path resolution.

    Args:
        urn: The URN to resolve
        data_path: Base data directory path
        check_alternates: Whether to check alternate path formats
        catalog_service: Enhanced catalog service
        xml_service: Enhanced XML service

    Returns:
        JSON response with path resolution information
    """
    result = {"urn": urn, "direct_path": {}, "catalog_path": {}, "xml_service_path": {}, "alternate_paths": []}

    # 1. Direct path transformation
    direct_path = direct_urn_to_path(urn, data_path)
    result["direct_path"]["path"] = direct_path
    result["direct_path"]["exists"] = os.path.exists(direct_path)
    result["direct_path"]["is_file"] = os.path.isfile(direct_path) if result["direct_path"]["exists"] else False

    # 2. Catalog service path
    text = catalog_service.get_text_by_urn(urn)
    if text:
        result["catalog_path"]["found"] = True
        result["catalog_path"]["path"] = text.path if hasattr(text, "path") and text.path else "No path in catalog"
        full_path = os.path.join(data_path, text.path) if hasattr(text, "path") and text.path else None
        if full_path:
            result["catalog_path"]["full_path"] = full_path
            result["catalog_path"]["exists"] = os.path.exists(full_path)
            result["catalog_path"]["is_file"] = os.path.isfile(full_path) if result["catalog_path"]["exists"] else False
    else:
        result["catalog_path"]["found"] = False
        result["catalog_path"]["path"] = None

    # 3. Try XML service path resolution
    try:
        # This might use different methods internally
        document = xml_service.load_document(urn)
        result["xml_service_path"]["loaded"] = True
        result["xml_service_path"]["document_id"] = str(document.id) if hasattr(document, "id") else "Unknown"

        # Try to get the actual file path used
        file_path = getattr(document, "file_path", None)
        if file_path:
            result["xml_service_path"]["path"] = str(file_path)
            result["xml_service_path"]["exists"] = os.path.exists(file_path)
            result["xml_service_path"]["is_file"] = os.path.isfile(file_path)
    except Exception as e:
        result["xml_service_path"]["loaded"] = False
        result["xml_service_path"]["error"] = str(e)

    # 4. Check alternate path formats if requested
    if check_alternates:
        # Parse URN to components
        parts = urn.split(":")
        if len(parts) >= 4:
            identifier = parts[3].split("#")[0]
            id_parts = identifier.split(".")
            if len(id_parts) >= 3:
                textgroup = id_parts[0]
                work = id_parts[1]
                version = id_parts[2]
                namespace = parts[2] if len(parts) >= 3 else "greekLit"

                # Try different path formats
                alternates = [
                    f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml",
                    f"{data_path}/{namespace}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml",
                    f"{data_path}/{textgroup}.{work}.{version}.xml",
                    f"{data_path}/{textgroup}/{textgroup}.{work}.{version}.xml",
                ]

                for alt_path in alternates:
                    alt_result = {
                        "path": alt_path,
                        "exists": os.path.exists(alt_path),
                        "is_file": os.path.isfile(alt_path) if os.path.exists(alt_path) else False,
                    }
                    result["alternate_paths"].append(alt_result)

    # Return JSON response
    return JSONResponse(content=result)


@router.get("/path-html/{urn}", response_class=HTMLResponse)
async def debug_path_resolution_html(
    urn: str,
    data_path: str = Query("data", description="Base path for data files"),
    check_alternates: bool = Query(True, description="Check alternate path formats"),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Debug URN to path resolution with HTML output.

    Args:
        urn: The URN to resolve
        data_path: Base data directory path
        check_alternates: Whether to check alternate path formats
        catalog_service: Enhanced catalog service
        xml_service: Enhanced XML service

    Returns:
        HTML response with path resolution information
    """
    # Get JSON data
    json_result = await debug_path_resolution(urn, data_path, check_alternates, catalog_service, xml_service)
    data = json_result.body

    # Convert to HTML
    html = f"""
    <html>
    <head>
        <title>Path Resolution Debug for {urn}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; margin-top: 20px; }}
            .path {{ font-family: monospace; background: #f5f5f5; padding: 5px; border-radius: 3px; }}
            .success {{ color: green; }}
            .failure {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>Path Resolution Debug</h1>
        <p><strong>URN:</strong> {urn}</p>

        <h2>Direct Path</h2>
        <p class="path">{data.get('direct_path', {}).get('path', 'N/A')}</p>
        <p>Exists: <span class="{'success' if data.get('direct_path', {}).get('exists', False) else 'failure'}">
            {data.get('direct_path', {}).get('exists', False)}
        </span></p>

        <h2>Catalog Path</h2>
        <p>Found in catalog:
            <span class="{'success' if data.get('catalog_path', {}).get('found', False) else 'failure'}">
                {data.get('catalog_path', {}).get('found', False)}
            </span>
        </p>

        <p>Path in catalog: <span class="path">
            {data.get('catalog_path', {}).get('path', 'N/A')}
        </span></p>

        <p>Full path: <span class="path">
            {data.get('catalog_path', {}).get('full_path', 'N/A')}
        </span></p>

        <p>Exists: <span class="{'success' if data.get('catalog_path', {}).get('exists', False) else 'failure'}">
            {data.get('catalog_path', {}).get('exists', False)}
        </span></p>

        <h2>XML Service Path</h2>
        <p>Loaded: <span class="{'success' if data.get('xml_service_path', {}).get('loaded', False) else 'failure'}">
            {data.get('xml_service_path', {}).get('loaded', False)}
        </span></p>

        <p>Path: <span class="path">{data.get('xml_service_path', {}).get('path', 'N/A')}</span></p>

        <p>Document ID: {data.get('xml_service_path', {}).get('document_id', 'N/A')}</p>

        <p>Exists: <span class="{'success' if data.get('xml_service_path', {}).get('exists', False) else 'failure'}">
            {data.get('xml_service_path', {}).get('exists', False)}
        </span></p>

        <h2>Alternate Paths</h2>
        <table>
            <tr>
                <th>Path</th>
                <th>Exists</th>
                <th>Is File</th>
            </tr>
            {"".join([
                f"<tr><td class='path'>{alt.get('path', 'N/A')}</td>"
                f"<td class='{'success' if alt.get('exists', False) else 'failure'}'>"
                f"{alt.get('exists', False)}</td>"
                f"<td class='{'success' if alt.get('is_file', False) else 'failure'}'>"
                f"{alt.get('is_file', False)}</td></tr>"
                for alt in data.get('alternate_paths', [])
            ])}
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
