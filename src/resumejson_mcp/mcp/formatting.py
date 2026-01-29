"""Common formatting utilities for MCP tool responses.

This module provides consistent formatting for tool output, reducing
duplication and ensuring a unified user experience across all tools.
"""

# Standard separator widths
SEPARATOR_WIDTH = 60
WIDE_SEPARATOR_WIDTH = 70


def header(title: str, emoji: str = "", width: int = SEPARATOR_WIDTH) -> str:
    """Format a section header with separator.
    
    Args:
        title: The header title
        emoji: Optional emoji prefix
        width: Width of the separator line
        
    Returns:
        Formatted header string
        
    Example:
        >>> header("JOB APPLICATION CREATED", "✓")
        '✓ JOB APPLICATION CREATED\\n============================================================\\n'
    """
    prefix = f"{emoji} " if emoji else ""
    return f"{prefix}{title}\n" + "=" * width + "\n"


def section(title: str, emoji: str = "", width: int = SEPARATOR_WIDTH) -> str:
    """Format a section divider with title.
    
    Args:
        title: The section title
        emoji: Optional emoji prefix
        width: Width of the separator line
        
    Returns:
        Formatted section string with leading newline
    """
    prefix = f"{emoji} " if emoji else ""
    return f"\n{prefix}{title}\n" + "-" * width + "\n"


def separator(width: int = SEPARATOR_WIDTH, char: str = "=") -> str:
    """Create a separator line.
    
    Args:
        width: Width of the separator
        char: Character to use for separator
        
    Returns:
        Separator string with surrounding newlines
    """
    return "\n" + char * width + "\n"


def bullet_list(items: list[str], indent: int = 2) -> str:
    """Format items as a bullet list.
    
    Args:
        items: List of strings to format
        indent: Number of spaces before bullet
        
    Returns:
        Formatted bullet list
    """
    if not items:
        return ""
    prefix = " " * indent + "• "
    return "\n".join(prefix + item for item in items)


def numbered_list(items: list[str], indent: int = 0) -> str:
    """Format items as a numbered list.
    
    Args:
        items: List of strings to format
        indent: Number of spaces before number
        
    Returns:
        Formatted numbered list
    """
    if not items:
        return ""
    prefix = " " * indent
    return "\n".join(f"{prefix}{i}. {item}" for i, item in enumerate(items, 1))


def key_value(key: str, value: str, indent: int = 0) -> str:
    """Format a key-value pair.
    
    Args:
        key: The label
        value: The value
        indent: Number of spaces before key
        
    Returns:
        Formatted "key: value" string
    """
    prefix = " " * indent
    return f"{prefix}{key}: {value}"


def success_message(title: str, details: list[str] | None = None) -> str:
    """Format a success message with optional details.
    
    Args:
        title: Main success message
        details: Optional list of detail lines
        
    Returns:
        Formatted success message
    """
    result = header(title, "✓")
    if details:
        result += "\n" + "\n".join(details) + "\n"
    return result


def error_message(title: str, details: list[str] | None = None, recovery: str | None = None) -> str:
    """Format an error message with optional recovery suggestions.
    
    Args:
        title: Main error message
        details: Optional list of detail lines
        recovery: Optional recovery suggestion
        
    Returns:
        Formatted error message
    """
    result = f"❌ ERROR: {title}\n"
    if details:
        result += "\n" + "\n".join(f"  {d}" for d in details) + "\n"
    if recovery:
        result += f"\nRECOVERY:\n{recovery}\n"
    return result


def next_steps(steps: list[str]) -> str:
    """Format a "next steps" section.
    
    Args:
        steps: List of next step descriptions
        
    Returns:
        Formatted next steps section
    """
    return "\n🎯 NEXT STEPS:\n" + numbered_list(steps)


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text with suffix if it was truncated
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_count(count: int, singular: str, plural: str | None = None) -> str:
    """Format a count with singular/plural noun.
    
    Args:
        count: The count
        singular: Singular form of the noun
        plural: Plural form (defaults to singular + 's')
        
    Returns:
        Formatted count string like "1 item" or "5 items"
    """
    if plural is None:
        plural = singular + "s"
    noun = singular if count == 1 else plural
    return f"{count} {noun}"
