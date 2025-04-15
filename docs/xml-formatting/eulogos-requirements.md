# Eulogos Text Formatting and Export Requirements

## Overview

The Eulogos project requires enhanced XML text formatting and multi-format export capabilities to make ancient Greek texts accessible for both online reading and offline use. This document outlines the specific requirements for implementing these features.

## 1. XML Formatting Requirements

### 1.1 Text Structure Preservation

- Maintain hierarchical structure of ancient texts (books, chapters, sections)
- Preserve paragraph and line breaks
- Maintain poetry line numbering and alignment
- Support nested elements (quotes, notes, references)
- Handle specialized TEI XML elements common in ancient texts

### 1.2 Reference Handling

- Parse and display hierarchical references (e.g., 1.1.5 for book.chapter.verse)
- Enable navigation between adjacent references
- Support citation and linking to specific text passages
- Extract and display reference metadata

### 1.3 Display Formatting

- Apply appropriate typography for ancient Greek texts
- Support token-level interactions for word analysis
- Maintain emphasis, italics, and other text styling
- Properly render specialized symbols and characters
- Display line numbers for poetry and verse texts

## 2. Export Functionality Requirements

### 2.1 Supported Export Formats

- PDF with proper typesetting and page layout
- ePub for e-readers and mobile devices
- MOBI/Kindle for Kindle devices
- Markdown for plain text editing and compatibility
- DOCX (Word) for academic and publishing workflows
- LaTeX for scholarly publications
- Standalone HTML for web access

### 2.2 Export Features

- Include document metadata (title, author, publisher)
- Generate table of contents for navigation
- Apply consistent typography and styling
- Preserve Greek characters and diacritical marks
- Include proper page breaks and section divisions
- Support customizable options for each format

### 2.3 User Interface

- Provide intuitive export options within the reader interface
- Allow format selection and customization
- Offer feedback for long-running export operations
- Handle errors gracefully with user-friendly messages

## 3. Technical Requirements

### 3.1 Code Structure

- Implement a modular, maintainable codebase
- Follow existing project architecture patterns
- Provide comprehensive documentation
- Include appropriate error handling
- Support testing with >85% code coverage

### 3.2 Performance

- Optimize for large documents
- Efficiently process complex XML structures
- Handle asynchronous operations for long-running exports
- Minimize memory usage for large texts
- Implement proper cleanup of temporary files

### 3.3 Compatibility

- Ensure Unicode compatibility for Greek text
- Support modern browsers and devices
- Generate standards-compliant output files
- Maintain accessibility standards
- Handle different operating systems for external tool integration

## 4. Implementation Approach

The implementation should follow the Reference Handling System approach outlined in the design document, which provides a comprehensive solution for TEI XML processing with support for:

- Hierarchical reference extraction
- Token-level processing
- Advanced HTML transformation
- Navigation between references

This foundation should be extended with export capabilities that leverage the enhanced XML processing to generate high-quality exports in various formats.

## 5. Expected Deliverables

1. **URN Model** (app/models/urn.py)
   - Pydantic model for parsing and manipulating CTS URNs
   - Comprehensive validation for URN components
   - Methods for URN transformation and file path resolution

2. **Enhanced XMLProcessorService**
   - Reference extraction and handling capabilities
   - Token-level text processing
   - HTML transformation with reference preservation

3. **ExportService** (app/services/export_service.py)
   - Support for all required formats (PDF, ePub, MOBI, Markdown, DOCX, LaTeX, HTML)
   - Format-specific processing and options
   - Proper error handling and dependency management

4. **Export API Endpoints** (app/routers/export.py)
   - Main export endpoint with format parameters
   - Option handling and validation
   - Proper error responses and content types

5. **UI Components**
   - Export button and dropdown in reader interface
   - Format selection and option controls
   - Progress indicators and error messaging

6. **Documentation**
   - Code documentation (docstrings, comments)
   - User documentation for export features
   - Developer documentation for system extension
   - Setup guides for external dependencies

7. **Test Suite**
   - Unit tests for all components
   - Integration tests for export workflows
   - Performance tests for large documents

## 6. Success Criteria

The implementation will be considered successful when:

1. TEI XML texts are properly formatted and readable in the browser
2. References are properly extracted and navigable
3. Exports maintain proper formatting and structure in all supported formats
4. The user interface provides intuitive access to export functionality
5. Performance is acceptable for large texts
6. All test cases pass successfully with >85% code coverage
7. Documentation is comprehensive and clear

## 7. Implementation Timeline

The implementation should follow this phased approach:

1. **Phase 1: Core Reference Handling (3-4 weeks)**
   - Implement URN model
   - Enhance XMLProcessorService
   - Create reader endpoints with reference navigation
   - Implement text display with proper formatting

2. **Phase 2: Export Service (2-3 weeks)**
   - Implement ExportService
   - Create export endpoints
   - Add export UI components
   - Test with various formats and options

3. **Phase 3: Enhancement and Optimization (1-2 weeks)**
   - Add advanced options for exports
   - Optimize performance for large texts
   - Improve error handling and user feedback
   - Add comprehensive tests

## 8. Dependencies and External Tools

The implementation will require these dependencies:

1. **Core Python Libraries**
   - FastAPI, Pydantic, lxml, Jinja2

2. **Export Libraries**
   - WeasyPrint (PDF)
   - ebooklib (ePub)
   - html2text (Markdown)
   - python-docx (DOCX)
   - beautifulsoup4 (HTML parsing)

3. **External Tools**
   - KindleGen or Calibre (MOBI)
   - XeLaTeX (LaTeX to PDF)

4. **Fonts**
   - SBL Greek or New Athena Unicode (Greek typography)

---

This requirements specification outlines the essential capabilities needed to enhance the Eulogos project with proper XML formatting and export functionality, ensuring ancient Greek texts are both readable online and available in multiple formats for offline use.
