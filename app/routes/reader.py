"""Routes for handling XML file display."""
from typing import Dict, Any, Optional
from xml.dom import minidom

from flask import Blueprint, render_template, abort, request
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
        # Get the raw parameter from query string
        raw_view = request.args.get("raw", "").lower() == "true"
        
        # Load XML content
        xml_content = xml_processor.load_xml_from_path(file_path)
        
        if raw_view:
            # Format raw XML with proper indentation for display
            dom = minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            # Wrap in a pre tag with appropriate class
            formatted_content = f'<pre class="xml-formatted">{pretty_xml}</pre>'
            references = []
        else:
            # Process XML for enhanced display
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