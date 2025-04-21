# Eulogos Documentation Map

This guide provides a map to all documentation related to the Eulogos hierarchical implementation, organized by implementation phase. Use this reference to find the right documentation at each stage of development.

## Implementation Workflow

```
Pre-Implementation → Core Implementation → Testing & Verification → Final Audit
```

## Pre-Implementation Phase

Start with these documents before making any code changes:

1. **[Implementation Plan](implementation/plan.md)** - *REQUIRED*  
   The master plan outlining the goals, architecture, and phased approach.

2. **[Migration Checklist](implementation/checklists/migration.md)** - *REQUIRED*  
   Step-by-step guide for the migration process.

3. **[Compatibility Guide](implementation/compatibility.md)** - *REQUIRED*  
   Essential requirements for maintaining compatibility across components.

4. **[Shell Scripts](implementation/code/shell/)**  
   Tools for automating parts of the implementation:
   - [purge_legacy.sh](implementation/code/shell/purge_legacy.sh) - For safely removing legacy files

## Core Implementation Phase

Use these code references during implementation:

1. **Python Components**
   - [Catalog Service](implementation/code/python/catalog_service.py) - *CRITICAL*
   - [Browse Router](implementation/code/python/browse_router.py) - *CRITICAL*
   - [Settings](implementation/code/python/settings.py)
   - [API Endpoint](implementation/code/python/api_endpoint.py)

2. **HTML Templates**
   - [Browse Template](implementation/code/html/browse.html) - *CRITICAL*
   - [Author List Partial](implementation/code/html/author_list.html)
   - [Search Results](implementation/code/html/search_results.html)

3. **JavaScript Implementation**
   - [Main.js](implementation/code/javascript/main.js) - *CRITICAL*  
     *Note: This must be fully implemented, not just copied as pseudocode.*

## Testing & Verification Phase

Use these documents to verify your implementation:

1. **[Verification Script](implementation/code/shell/verify_impl.sh)** - *REQUIRED*  
   Automated verification of the implementation integrity.

2. **[Basic Tests](implementation/code/python/basic_tests.py)** - *REQUIRED*  
   Minimum test suite that should pass before deployment.

3. **[CI Workflow](ci/ci_workflow.yml)**  
   GitHub Actions workflow for continuous integration.

## Final Audit Phase

Before deployment, perform a final audit using:

1. **[Audit Checklist](implementation/checklists/audit.md)** - *REQUIRED*  
   Comprehensive verification of all aspects of the implementation.

## Developer Reference

Additional resources for developers:

1. **[Contributing Guide](guides/contributing.md)**  
   Guidelines for future contributors to maintain consistency.

## Implementation Priority Legend

* **REQUIRED**: Must be consulted and followed
* **CRITICAL**: Essential for successful implementation
* Unlabeled: Helpful but supplementary

## Timeline Reference

| Phase | Estimated Duration | Key Documents |
|-------|-------------------|---------------|
| Pre-Implementation | 0.5 day | Plan, Migration Checklist, Compatibility Guide |
| Core Implementation | 2 days | Catalog Service, Browse Router, Browse Template, Main.js |
| Testing & Verification | 1 day | Verification Script, Basic Tests |
| Final Audit | 0.5 day | Audit Checklist |

Total estimated timeline: 4 days