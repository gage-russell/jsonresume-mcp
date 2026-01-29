"""Common error messages and validation helpers.

This module provides consistent error messages and validation patterns used
across all MCP tools to eliminate duplication.
"""

from typing import Any


def error_not_found(entity_type: str, entity_id: str, list_tool: str = "") -> str:
    """Generate a standardized 'not found' error message.
    
    Args:
        entity_type: Type of entity (e.g., "skill", "work position", "application")
        entity_id: The ID that wasn't found
        list_tool: Optional name of the tool to list all items
    
    Returns:
        Formatted error message
    
    Example:
        error_not_found("skill", "abc123", "get_all_skills")
        # "❌ No skill found with ID: abc123\n\nUse get_all_skills to see available items."
    """
    msg = f"❌ No {entity_type} found with ID: {entity_id}"
    
    if list_tool:
        msg += f"\n\nUse {list_tool} to see available items."
    
    return msg


def error_invalid_choice(field_name: str, provided_value: str, valid_choices: list[str]) -> str:
    """Generate error message for invalid enum/choice values.
    
    Args:
        field_name: Name of the field
        provided_value: The invalid value provided
        valid_choices: List of valid choices
    
    Returns:
        Formatted error message
    
    Example:
        error_invalid_choice("priority", "urgent", ["critical", "high", "medium", "low"])
    """
    choices_str = ", ".join(valid_choices)
    return f"""❌ Invalid {field_name}: {provided_value}

Valid {field_name}s: {choices_str}"""


def error_missing_field(entity_type: str, field_name: str, setup_tool: str = "") -> str:
    """Generate error for missing required field or entity.
    
    Args:
        entity_type: Type of entity
        field_name: Name of missing field
        setup_tool: Optional setup tool to run
    
    Returns:
        Formatted error message
    """
    msg = f"❌ No {entity_type} found"
    
    if field_name:
        msg += f": missing {field_name}"
    
    if setup_tool:
        msg += f"\n\nUse {setup_tool} first to initialize."
    
    return msg


def error_file_not_found(file_type: str = "Experience", init_tool: str = "initialize_experience") -> str:
    """Generate error for missing experience/application file.
    
    Args:
        file_type: Type of file missing
        init_tool: Tool to initialize the file
    
    Returns:
        Formatted error message
    """
    return f"❌ {file_type} file not found. Run {init_tool}() first."


def validate_non_empty_list(items: list[Any], entity_name: str) -> str | None:
    """Validate that a list is not empty.
    
    Args:
        items: List to validate
        entity_name: Name for error message (e.g., "skills", "projects")
    
    Returns:
        Error message if empty, None if valid
    """
    if not items:
        return f"❌ No {entity_name} provided to add"
    return None


def success_message(action: str, entity_type: str, details: str = "") -> str:
    """Generate standardized success message.
    
    Args:
        action: Action performed (e.g., "added", "updated", "deleted")
        entity_type: Type of entity
        details: Optional additional details
    
    Returns:
        Formatted success message
    
    Example:
        success_message("added", "skill category", "Programming Languages")
        # "✓ SKILL CATEGORY ADDED\n\nProgramming Languages"
    """
    header = f"✓ {entity_type.upper()} {action.upper()}"
    
    if details:
        return f"{header}\n\n{details}"
    
    return header
