"""Blueprint for XML file reading and display functionality."""
from typing import Dict, List, Optional

from flask import Blueprint, render_template, abort
from werkzeug.exceptions import NotFound

from app.services.xml_processor import XMLProcessorService

bp = Blueprint("reader", __name__)
xml_processor = XMLProcessorService()


@bp.route("/view/<path:file_path>")
def view(file_path: str) -> str:
    """Display formatted XML content and references for a given file path.
    
    Args:
        file_path: Path to the XML file relative to the data directory
        
    Returns:
        Rendered template with XML content and references
        
    Raises:
        NotFound: If the specified XML file does not exist
    """
    try:
        raw_xml = xml_processor.load_xml_from_path(file_path)
        formatted_xml = xml_processor.format_xml_for_display(raw_xml)
        references = xml_processor.get_references(raw_xml)
        
        return render_template(
            "reader/view.html",
            content=formatted_xml,
            references=references,
            file_path=file_path
        )
    except FileNotFoundError:
        abort(404) 