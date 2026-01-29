"""Shared utilities for MCP tools."""

import json
from functools import wraps
from typing import Callable, Any


def safe_experience_operation(func: Callable) -> Callable:
    """Decorator for consistent error handling in experience operations.
    
    Catches common errors and returns user-friendly messages instead of
    raising exceptions that could confuse the AI agent.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            if "experience" in str(e).lower():
                return "❌ Experience file not found. Run initialize_experience() first."
            return f"❌ File not found: {str(e)}"
        except json.JSONDecodeError as e:
            return f"❌ Experience file is corrupted (invalid JSON). Check file integrity.\nError: {str(e)}"
        except PermissionError as e:
            return f"❌ Permission denied accessing file: {str(e)}"
        except ValueError as e:
            # Re-raise ValueError as it's often used for "not found" cases
            # that tools handle specifically
            raise
        except Exception as e:
            return f"❌ Unexpected error: {type(e).__name__}: {str(e)}"
    return wrapper


def format_list_result(
    items: list,
    header: str,
    format_item: Callable[[Any], str],
    empty_message: str = "No items found.",
    next_steps: str | None = None,
) -> str:
    """Format a list of items for display.
    
    Args:
        items: List of items to format
        header: Header text (e.g., "📋 WORK EXPERIENCE")
        format_item: Function to format each item
        empty_message: Message to show if list is empty
        next_steps: Optional next steps text
    
    Returns:
        Formatted string output
    """
    if not items:
        result = empty_message
        if next_steps:
            result += f"\n\n{next_steps}"
        return result
    
    result = "\n".join([f"{header}\n" + "=" * 60] + [format_item(item) for item in items])
    if next_steps:
        result += f"\n\n{next_steps}"
    
    return result


class ToolResponse:
    """Structured response from a tool operation.
    
    Provides consistent formatting for tool outputs with success/failure
    indication, messages, and next steps.
    """
    
    def __init__(
        self,
        success: bool,
        message: str,
        data: dict | None = None,
        next_steps: list[str] | None = None,
        warnings: list[str] | None = None,
    ):
        self.success = success
        self.message = message
        self.data = data
        self.next_steps = next_steps or []
        self.warnings = warnings or []
    
    def __str__(self) -> str:
        """Format as string for tool output."""
        icon = "✓" if self.success else "❌"
        result = f"{icon} {self.message}\n"
        
        if self.warnings:
            result += "\n⚠️  WARNINGS:\n"
            for warning in self.warnings:
                result += f"  • {warning}\n"
        
        if self.next_steps:
            result += "\n🎯 NEXT STEPS:\n"
            for step in self.next_steps:
                result += f"  • {step}\n"
        
        return result
    
    @classmethod
    def success(cls, message: str, **kwargs) -> "ToolResponse":
        """Create a success response."""
        return cls(success=True, message=message, **kwargs)
    
    @classmethod
    def error(cls, message: str, **kwargs) -> "ToolResponse":
        """Create an error response."""
        return cls(success=False, message=message, **kwargs)
