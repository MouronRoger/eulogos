# Eulogos Documentation

## Overview

This directory contains all documentation for the Eulogos Ancient Greek Text Repository, with a focus on the hierarchical browser implementation. The documentation is organized to support a smooth and efficient implementation process.

## Core Principles

All implementation must adhere to these fundamental principles:

1. **Single Source of Truth**: `integrated_catalog.json` is the ONLY source for text paths
2. **Canonical References**: ALL text identification uses direct file paths ONLY
3. **No Dual Tracking**: One implementation, one code path, zero legacy compatibility

## Documentation Structure

```
docs/hierarchical/
├── README.md                       # This document
├── implementation/                 # Core implementation guides
│   ├── plan.md                     # Main implementation plan
│   ├── checklists/                 # Verification checklists
│   ├── code/                       # Reference implementations
│   │   ├── python/                 # Python components
│   │   ├── javascript/             # JavaScript components
│   │   ├── html/                   # HTML templates
│   │   └── shell/                  # Shell scripts
│   └── compatibility.md            # Compatibility requirements
├── ci/                             # CI configuration
└── guides/                         # Developer guides
```

## How to Use This Documentation

Follow this recommended sequence:

1. Start with [implementation/plan.md](implementation/plan.md) to understand the overall approach
2. Review [implementation/compatibility.md](implementation/compatibility.md) for critical compatibility requirements
3. Follow the migration process using [implementation/checklists/migration.md](implementation/checklists/migration.md)
4. Use the reference implementations in the code directory during development
5. Verify your implementation with [implementation/code/shell/verify_impl.sh](implementation/code/shell/verify_impl.sh)
6. Perform a final audit using [implementation/checklists/audit.md](implementation/checklists/audit.md)

For a more detailed map of which documents to use at each implementation stage, see the [Documentation Map](documentation-map.md).

## Implementation Timeline

The implementation is structured as a series of focused bursts:

- **Burst A (2 days)**: Core Replacement
  - Replace core files (catalog service, router, templates)
  - Update API endpoint
  - Delete obsolete files
  - Initial smoke testing

- **Burst B (1 day)**: UI Polish & State Management
  - Implement JavaScript functionality
  - Test UI components
  - Cross-browser verification

- **Burst C (1 day)**: Testing & Documentation
  - Create test suite
  - Update documentation
  - Final verification

## Tools & Utilities

- [purge_legacy.sh](implementation/code/shell/purge_legacy.sh): Script to safely remove legacy files
- [verify_impl.sh](implementation/code/shell/verify_impl.sh): Verification script to check implementation

## Maintaining Documentation

When updating this codebase:

1. Keep documentation in sync with code changes
2. Update checklists to reflect new requirements
3. Ensure all examples use consistent canonical paths
4. Follow the style guide in [guides/contributing.md](guides/contributing.md)