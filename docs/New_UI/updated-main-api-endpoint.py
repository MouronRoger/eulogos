@app.get("/api/catalog")
async def get_catalog(catalog_service=Depends(get_catalog_service)):
    """API endpoint to get the full catalog in hierarchical structure.
    
    Returns a dictionary with both hierarchical and list representations
    for maximum compatibility.
    """
    # Get hierarchical structure
    hierarchical = catalog_service.get_hierarchical_texts(include_archived=True)
    
    # Also include the full text list for backward compatibility
    texts = []
    for author_data in hierarchical.values():
        for work_data in author_data["works"].values():
            texts.extend(work_data["texts"])
    
    return {
        "hierarchical": hierarchical,
        "texts": [text.model_dump() for text in texts]  # Convert Text objects to dictionaries
    }