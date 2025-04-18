"""Routes for handling XML file display."""
from typing import Dict, Any

from flask import Blueprint, render_template, abort
from app.services.xml_processor import XMLProcessorService

bp = Blueprint("reader", __name__)
xml_processor = XMLProcessorService()


@bp.route("/read/<path:file_path>")
def read_xml(file_path: str) -> str:
    """Display XML file content.
    
    Args:
        file_path: Path to the XML file relative to the data directory
        
    Returns:
        Rendered template with XML content
        
    Raises:
        404: If file not found
    """
    try:
        xml_content = xml_processor.load_xml_from_path(file_path)
        formatted_content = xml_processor.format_xml_for_display(xml_content)
        references = xml_processor.get_references(xml_content, file_path)
        
        return render_template(
            "reader.html",
            title="XML Reader",
            path=file_path,
            content=formatted_content,
            references=references
        )
    except FileNotFoundError:
        abort(404, description=f"XML file not found: {file_path}") 