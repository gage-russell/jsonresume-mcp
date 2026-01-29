"""Shared helper functions for all experience sections.

This module contains common utilities used across work, skills, projects, and education
to eliminate code duplication and provide consistent behavior.
"""

from typing import Any, Callable, TypeVar
from uuid import uuid4

from resumejson_mcp.constants import MAX_ID_COLLISION_RETRIES
from resumejson_mcp.lib.experience.models import (
    Education,
    MCPEducationDetails,
    MCPProjectDetails,
    MCPSkillDetails,
    MCPWorkDetails,
    Project,
    Skill,
    Work,
)

T = TypeVar('T', Work, Skill, Project, Education)
MCP_T = TypeVar('MCP_T', MCPWorkDetails, MCPSkillDetails, MCPProjectDetails, MCPEducationDetails)


def ensure_mcp_id(
    item: T,
    mcp_details_class: type[MCP_T],
) -> None:
    """Ensure an item has mcp_details with a valid ID.
    
    This is a generic function that works for all experience types (Work, Skill,
    Project, Education) by accepting the appropriate MCPDetails class.
    
    Args:
        item: The item to ensure has an ID (Work, Skill, Project, or Education)
        mcp_details_class: The MCPDetails class to instantiate if needed
    
    Example:
        ensure_mcp_id(work, MCPWorkDetails)
        ensure_mcp_id(skill, MCPSkillDetails)
    """
    if not item.mcp_details:
        item.mcp_details = mcp_details_class(id=str(uuid4()))
    elif not item.mcp_details.id:
        item.mcp_details.id = str(uuid4())


def ensure_nested_ids(items: list[Any], id_field: str = "id") -> None:
    """Ensure all items in a nested list have IDs.
    
    Used for bullets, major_projects, and other nested collections.
    
    Args:
        items: List of objects that need IDs
        id_field: Name of the ID field (default: "id")
    """
    for item in items:
        if not getattr(item, id_field, None):
            setattr(item, id_field, str(uuid4()))


def handle_id_collision(
    item: T,
    get_by_id_func: Callable[[str], Any],
    regenerate_id_func: Callable[[T], None],
    max_retries: int = MAX_ID_COLLISION_RETRIES,
) -> None:
    """Handle ID collision by regenerating until unique.
    
    This provides consistent ID collision handling across all add operations.
    
    Args:
        item: The item with the potentially colliding ID
        get_by_id_func: Function to check if ID exists (raises ValueError if not found)
        regenerate_id_func: Function to regenerate the ID
        max_retries: Maximum attempts to regenerate (default: 3)
    """
    for _ in range(max_retries):
        try:
            # Try to get existing item with this ID
            get_by_id_func(item.mcp_details.id)
            # If we got here, ID exists - regenerate
            regenerate_id_func(item)
        except ValueError:
            # ID doesn't exist - we're good
            break


def format_tags_line(tags: list[str] | None) -> str:
    """Format a tags line for display.
    
    Args:
        tags: List of tags or None
    
    Returns:
        Formatted string with tags or empty string
    """
    if not tags:
        return ""
    return f"🏷️  TAGS: {', '.join(tags)}\n"


def format_missing_info_section(missing: list[str]) -> str:
    """Format a missing information section.
    
    Args:
        missing: List of missing items
    
    Returns:
        Formatted warning section or empty string
    """
    if not missing:
        return ""
    
    return f"""
⚠️  MISSING/INCOMPLETE INFORMATION:
{chr(10).join(f'  • {m}' for m in missing)}

⚠️  IMPORTANT: Ask targeted follow-up questions to complete this information.
"""


def build_next_steps(
    entity_name: str,
    has_missing: bool,
    additional_steps: str = ""
) -> str:
    """Build standardized next steps section.
    
    Args:
        entity_name: Name of the entity (e.g., "work position", "project")
        has_missing: Whether there's missing information
        additional_steps: Additional custom steps to include
    
    Returns:
        Formatted next steps section
    """
    next_steps = f"""
🎯 NEXT STEPS (REQUIRED):
1. Show user the captured information above
2. Ask: "Does this look correct for your {entity_name}?"
"""
    
    if has_missing:
        next_steps += """3. ⚠️  CRITICAL: This entry is missing important information.
   Ask specific follow-up questions to complete it.
4. Update the entry once you have more information
"""
    else:
        next_steps += """3. ✓ This entry looks complete!
"""
    
    if additional_steps:
        final_step = 5 if has_missing else 4
        next_steps += f"{final_step}. {additional_steps}\n"
    
    return next_steps
