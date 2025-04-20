# Docker Compatibility Notes

The simplified Eulogos application is designed to be compatible with your existing Docker setup. Here are important considerations to ensure smooth integration:

## Dockerfile Compatibility

Your existing Dockerfile should continue to work without changes since:

1. **Directory Structure**: The simplified app maintains the same basic structure:
   - `app/` folder containing the application code
   - Standard Python module organization

2. **Dependencies**: The simplified application uses similar dependencies:
   - FastAPI
   - Uvicorn
   - Jinja2
   - Pydantic (maintaining v1 compatibility)

3. **Entrypoint**: The application startup remains compatible:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Volume Mappings

If your Docker setup uses volume mappings for data files, they should continue to work:

1. **Data Directory**: The simplified app still expects the `data/` directory containing XML files
2. **Catalog File**: The application still uses `integrated_catalog.json` as the catalog file

## Environment Variables

The simplified app supports the following environment variables (prefixed with `EULOGOS_`):

- `EULOGOS_DATA_DIR`: Path to the data directory (default: "data")
- `EULOGOS_CATALOG_PATH`: Path to the catalog file (default: "integrated_catalog.json")
- `EULOGOS_DEBUG`: Enable debug mode (default: false)

## Verification Steps

After implementing the simplified application, verify Docker compatibility:

1. **Build the Docker image**:
   ```bash
   docker build -t eulogos .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/data:/app/data eulogos
   ```

3. **Verify catalog generation**:
   ```bash
   docker exec -it <container_id> python -m app.services.canonical_catalog_builder --data-dir=data --output=integrated_catalog.json
   ```

4. **Access the application**:
   Open a browser and navigate to `http://localhost:8000`

## Potential Issues & Solutions

1. **Catalog Not Found**:
   - Run the catalog builder before starting the application
   - Verify catalog file path matches the expected location

2. **XML Files Not Found**:
   - Ensure data volume is correctly mounted
   - Check data directory path configuration

3. **Missing Dependencies**:
   - If new dependencies were added, update the requirements.txt file and rebuild the Docker image
