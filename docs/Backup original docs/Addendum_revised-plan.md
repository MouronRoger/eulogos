# Revised Eulogos Rebuild Plan

## Modifications to Incorporate Existing Components

This revised plan preserves your existing canonical catalog builder and Docker setup, which represent significant value and effort already invested in the project.

### 1. Keep Existing Components:

- **Keep the Canonical Catalog Builder**: The existing `canonical_catalog_builder.py` is already well-structured and does its job effectively. We'll use it as-is without modification.
- **Preserve Docker Setup**: Your Docker configuration will be maintained without changes.

### 2. Simplified Implementation Approach:

Since we're keeping the canonical catalog builder, our focus shifts to building the simplified application layer that correctly utilizes the catalog output file (`integrated_catalog.json`).

## Implementation Plan

### Phase 1: Core Structure Setup

1. **Project Structure Preparation**:
   - Keep the existing directory structure to maintain compatibility with Docker
   - Leave `canonical_catalog_builder.py` in its current location

2. **Create Minimal Models**:
   - Implement simple models that work directly with paths as IDs
   - Use `integrated_catalog.json` as the data source without modification

3. **Build Direct XML Service**:
   - Create a service that loads XML directly by path
   - Focus on simple transformation to HTML

### Phase 2: Web Interface

4. **FastAPI Application**:
   - Build simple routes for browsing and reading
   - Ensure Docker compatibility

5. **Templates and UI**:
   - Implement minimal, effective templates
   - Support both path-based browsing and reading

### Phase 3: Docker Integration

6. **Verify Docker Compatibility**:
   - Ensure all new components work with existing Docker setup
   - Test Docker build and run processes

## Implementation Strategy

1. **Selective Replacement**:
   - Keep valuable existing components (catalog builder, Docker setup)
   - Replace just the URN processing and complex abstraction layers

2. **Phased Testing**:
   - Test with existing catalog output file
   - Verify Docker functionality throughout

3. **Documentation**:
   - Update only the necessary documentation
   - Maintain references to existing processes for catalog generation

## Migration Path

1. **Backup Current System**:
   - Create a backup of the current codebase
   - Document the current Docker setup if not already done

2. **Implement New Components**:
   - Add new simplified code alongside existing structure
   - Gradually switch over to new code paths

3. **Verification**:
   - Test with real XML data
   - Verify Docker deployment

This approach preserves your investment in the canonical catalog builder and Docker setup while still achieving the goal of simplifying the codebase by removing URN processing and unnecessary abstraction layers.
