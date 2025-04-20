"""Routers for the Eulogos application."""

from app.routers.browse import router as browse_router
from app.routers.read import router as read_router

__all__ = ["browse_router", "read_router"] 