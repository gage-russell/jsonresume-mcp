"""Dependency injection for resumejson-mcp tools.

This module provides lazy-loaded dependencies that tools can use via FastMCP's
Depends() mechanism. Using DI instead of instantiating stores in every function:
- Reduces boilerplate code
- Makes testing easier (can mock dependencies)
- Enables future caching/pooling if needed
- Centralizes store configuration
"""

from functools import lru_cache

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.applications.application_store import ApplicationStore
from resumejson_mcp.lib.pending_actions import PendingActionsTracker
from resumejson_mcp.templates.templates_store import TemplatesStore


@lru_cache(maxsize=1)
def get_experience_store() -> ExperienceStore:
    """Get the singleton ExperienceStore instance.
    
    Usage in tools:
        from fastmcp.dependencies import Depends
        from resumejson_mcp.dependencies import get_experience_store
        
        @tool
        def my_tool(store: ExperienceStore = Depends(get_experience_store)):
            return store.get_all_work()
    """
    return ExperienceStore()


@lru_cache(maxsize=1)
def get_application_store() -> ApplicationStore:
    """Get the singleton ApplicationStore instance."""
    return ApplicationStore()


@lru_cache(maxsize=1)
def get_templates_store() -> TemplatesStore:
    """Get the singleton TemplatesStore instance."""
    return TemplatesStore()


def get_pending_tracker() -> PendingActionsTracker:
    """Get the PendingActionsTracker singleton.
    
    Note: PendingActionsTracker already implements singleton pattern,
    but this provides a consistent interface.
    """
    from resumejson_mcp.lib.pending_actions import get_tracker
    return get_tracker()


def clear_caches() -> None:
    """Clear all cached stores. Useful for testing."""
    get_experience_store.cache_clear()
    get_application_store.cache_clear()
    get_templates_store.cache_clear()
