"""Router for exporting texts in various formats."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from loguru import logger

from app.dependencies import get_catalog_service, get_xml_processor_service
from app.models.urn import URN
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService

router = APIRouter(
    prefix="/export",
    tags=["export"],
)


@router.get("/{format}/{urn}")
async def export_text(
    format: str,
    urn: str,
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_processor: XMLProcessorService = Depends(get_xml_processor_service),
):
    """Export text in the specified format.

    Args:
        format: Export format (pdf, epub, mobi, markdown, docx, latex, html)
        urn: Text URN to export
        request: Request object
        catalog_service: Catalog service
        xml_processor: XML processor service

    Returns:
        Exported text as a downloadable file

    Raises:
        HTTPException: If format is invalid or text not found
    """
    try:
        # Validate format
        valid_formats = ["pdf", "epub", "mobi", "markdown", "docx", "latex", "html"]
        if format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {format}")

        # Parse URN and load text metadata
        urn_obj = URN(value=urn)
        text = catalog_service.get_text_by_urn(urn)

        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

        try:
            # Load XML content
            xml_root = xml_processor.load_xml(urn_obj)

            # Get reference if in URN
            reference = urn_obj.reference

            # Get text content
            file_path = xml_processor.resolve_urn_to_file_path(urn_obj)

            # Extract text content based on format
            if format == "html":
                # Transform to HTML
                content = xml_processor.transform_to_html(xml_root, reference)
                filename = f"{text.work_name.replace(' ', '_')}.html"

                # Return HTML response
                return HTMLResponse(
                    content=f"""<!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>{text.work_name}</title>
                        <style>
                            body {{ font-family: serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                            .text-part {{ margin-bottom: 10px; }}
                            .section-num {{ font-weight: bold; margin-right: 10px; }}
                            h1 {{ font-size: 24px; margin-bottom: 20px; }}
                            h2 {{ font-size: 20px; margin-bottom: 15px; }}
                        </style>
                    </head>
                    <body>
                        <h1>{text.group_name} - {text.work_name}</h1>
                        {content}
                    </body>
                    </html>""",
                    media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

            elif format == "markdown":
                # Extract raw text and convert to markdown
                raw_content = xml_processor.extract_text_content(file_path)
                # Convert HTML to markdown (simplified)
                md_content = f"# {text.group_name} - {text.work_name}\n\n"
                md_content += raw_content.replace("<p>", "").replace("</p>", "\n\n").replace("<br>", "\n")
                md_content = md_content.replace("<h3>", "### ").replace("</h3>", "\n")
                md_content = md_content.replace("<div>", "").replace("</div>", "\n")

                # Clean up any remaining HTML tags with a simple regex
                import re

                md_content = re.sub(r"<[^>]*>", "", md_content)

                filename = f"{text.work_name.replace(' ', '_')}.md"

                return Response(
                    content=md_content,
                    media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

            elif format == "latex":
                # Extract raw text and convert to LaTeX
                raw_content = xml_processor.extract_text_content(file_path)

                # Convert HTML to LaTeX (simplified)
                latex_content = r"\documentclass{article}" + "\n"
                latex_content += r"\usepackage[utf8]{inputenc}" + "\n"
                latex_content += r"\usepackage{fontspec}" + "\n"
                latex_content += r"\usepackage{polyglossia}" + "\n"

                # Set language based on text
                if text.language == "grc":
                    latex_content += r"\setmainlanguage{greek}" + "\n"
                elif text.language == "lat":
                    latex_content += r"\setmainlanguage{latin}" + "\n"
                else:
                    latex_content += r"\setmainlanguage{english}" + "\n"

                latex_content += r"\title{" + text.work_name + r"}" + "\n"
                latex_content += r"\author{" + text.group_name + r"}" + "\n"
                latex_content += r"\begin{document}" + "\n"
                latex_content += r"\maketitle" + "\n\n"

                # Convert content
                content_latex = raw_content.replace("<p>", "").replace("</p>", "\n\n")
                content_latex = content_latex.replace("<h3>", r"\section{").replace("</h3>", "}")
                content_latex = content_latex.replace("<div>", "").replace("</div>", "\n")
                content_latex = content_latex.replace("<br>", r" \\ ")

                # Clean up any remaining HTML tags
                content_latex = re.sub(r"<[^>]*>", "", content_latex)

                latex_content += content_latex
                latex_content += r"\end{document}"

                filename = f"{text.work_name.replace(' ', '_')}.tex"

                return Response(
                    content=latex_content,
                    media_type="application/x-latex",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

            elif format == "pdf":
                # For PDF export, we'll use a placeholder implementation
                # In a real implementation, you'd use a library like WeasyPrint, xhtml2pdf, or call a service
                return HTMLResponse(
                    content="""
                    <html>
                    <head><title>PDF Export</title></head>
                    <body>
                        <h1>PDF Export Not Implemented</h1>
                        <p>PDF export functionality requires additional dependencies like WeasyPrint or xhtml2pdf.</p>
                        <p>To implement PDF export:</p>
                        <ol>
                            <li>Install required dependencies (e.g., <code>pip install weasyprint</code>)</li>
                            <li>Update this route to use the PDF generation library</li>
                        </ol>
                    </body>
                    </html>
                    """,
                    status_code=501,  # Not Implemented
                )

            elif format in ["epub", "mobi", "docx"]:
                # These formats require additional libraries like ebooklib, docx
                return HTMLResponse(
                    content=f"""
                    <html>
                    <head><title>{format.upper()} Export</title></head>
                    <body>
                        <h1>{format.upper()} Export Not Implemented</h1>
                        <p>{format.upper()} export functionality requires additional dependencies.</p>
                        <p>To implement {format.upper()} export:</p>
                        <ol>
                            <li>Install required dependencies (e.g., <code>pip install ebooklib</code> for ePub)</li>
                            <li>Update this route to use the appropriate library</li>
                        </ol>
                    </body>
                    </html>
                    """,
                    status_code=501,  # Not Implemented
                )

            else:
                # This shouldn't happen due to validation above
                raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")

        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Text file not found for URN: {urn}")

    except Exception as e:
        logger.error(f"Error exporting text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting text: {str(e)}")
