#!/usr/bin/env python
"""Utility script to fix parameter names in enhanced_export_service.py."""

import re

# Read the file
with open('app/services/enhanced_export_service.py', 'r') as f:
    content = f.read()

# Replace function declarations
content = re.sub(r'def export_to_\w+\(self, text_id: str', r'def export_to_\g<0>', content)
content = re.sub(r'def export_to_\w+\(self, urn:', r'def export_to_\g<0>[:-4]text_id:', content)

# Replace urn parameters in docstrings
content = re.sub(r'Args:\s+urn: URN of the text', r'Args:\n        text_id: ID of the text', content)

# Replace urn variable usage in functions
content = re.sub(r'\bmetadata = self\._get_metadata\(urn\)', r'metadata = self._get_metadata(text_id)', content)
content = re.sub(r'\bhtml_path = self\.export_to_html\(urn,', r'html_path = self.export_to_html(text_id,', content)
content = re.sub(r'\bcontent = self\.xml_service\.transform_to_html\(urn,', r'content = self.xml_service.transform_to_html(text_id,', content)
content = re.sub(r'\bdocument = self\.xml_service\.load_document\(urn\)', r'document = self.xml_service.load_document(text_id)', content)
content = re.sub(r'\boutput_path = self\._get_output_path\(urn,', r'output_path = self._get_output_path(text_id,', content)

# Update _get_metadata method
content = re.sub(r'def _get_metadata\(self, text_id: str\)', r'def _get_metadata(self, text_id: str)', content)
content = re.sub(r'text = self\.catalog_service\.get_text_by_urn\(urn\)', r'text = self.catalog_service.get_text_by_id(text_id)', content)

# Update _get_output_path method
content = re.sub(r'def _get_output_path\(self, urn: Union\[str, EnhancedURN\]', r'def _get_output_path(self, text_id: Union[str, EnhancedURN]', content)

# Write the updated content back to the file
with open('app/services/enhanced_export_service.py.fixed', 'w') as f:
    f.write(content)

print("Fixed file written to app/services/enhanced_export_service.py.fixed") 