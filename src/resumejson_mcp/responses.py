"""
Standardized response format for ResumeJSON-MCP tools.

Provides consistent structure across all tool responses for better
parsing, error handling, and user experience.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResponseStatus(Enum):
    """Status of a tool response."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ToolResponse:
    """Standardized response structure for all tools.
    
    Attributes:
        status: SUCCESS, ERROR, WARNING, or INFO
        message: Main message to display
        data: Optional structured data (for programmatic use)
        next_steps: Suggested actions the AI should take next
        pending_actions: New pending actions created by this operation
        details: Additional details or breakdown
    """
    status: ResponseStatus
    message: str
    data: dict[str, Any] | None = None
    next_steps: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    
    def format(self) -> str:
        """Format the response as a human-readable string."""
        # Status emoji and message
        emoji = {
            ResponseStatus.SUCCESS: "✅",
            ResponseStatus.ERROR: "❌",
            ResponseStatus.WARNING: "⚠️",
            ResponseStatus.INFO: "ℹ️",
        }[self.status]
        
        lines = [f"{emoji} {self.message}"]
        
        # Details section
        if self.details:
            lines.append("")
            lines.extend(f"  • {detail}" for detail in self.details)
        
        # Pending actions section
        if self.pending_actions:
            lines.append("")
            lines.append("📋 PENDING ACTIONS:")
            for action in self.pending_actions:
                lines.append(f"  🔸 {action}")
        
        # Next steps section
        if self.next_steps:
            lines.append("")
            lines.append("➡️ NEXT STEPS:")
            for i, step in enumerate(self.next_steps, 1):
                lines.append(f"  {i}. {step}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return self.format()


def success(
    message: str,
    data: dict[str, Any] | None = None,
    details: list[str] | None = None,
    next_steps: list[str] | None = None,
    pending_actions: list[str] | None = None,
) -> str:
    """Create a success response.
    
    Args:
        message: Main success message
        data: Optional structured data
        details: Additional details as bullet points
        next_steps: Suggested next actions
        pending_actions: New pending actions created
        
    Returns:
        Formatted response string
    """
    return ToolResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        details=details or [],
        next_steps=next_steps or [],
        pending_actions=pending_actions or [],
    ).format()


def error(
    message: str,
    details: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> str:
    """Create an error response.
    
    Args:
        message: Main error message
        details: Additional error details
        next_steps: Suggested recovery actions
        
    Returns:
        Formatted response string
    """
    return ToolResponse(
        status=ResponseStatus.ERROR,
        message=message,
        details=details or [],
        next_steps=next_steps or [],
    ).format()


def warning(
    message: str,
    details: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> str:
    """Create a warning response.
    
    Args:
        message: Main warning message
        details: Additional warning details
        next_steps: Suggested actions to address warning
        
    Returns:
        Formatted response string
    """
    return ToolResponse(
        status=ResponseStatus.WARNING,
        message=message,
        details=details or [],
        next_steps=next_steps or [],
    ).format()


def info(
    message: str,
    data: dict[str, Any] | None = None,
    details: list[str] | None = None,
) -> str:
    """Create an info response.
    
    Args:
        message: Main info message
        data: Optional structured data
        details: Additional details
        
    Returns:
        Formatted response string
    """
    return ToolResponse(
        status=ResponseStatus.INFO,
        message=message,
        data=data,
        details=details or [],
    ).format()


# Tool category tags - use these for consistent categorization
class ToolTags:
    """Standard tags for categorizing tools."""
    
    # Primary categories
    SETUP = "setup"
    EXPERIENCE = "experience"
    WORK = "work"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    BASICS = "basics"
    TEMPLATES = "templates"
    APPLICATIONS = "applications"
    WORKFLOW = "workflow"
    SEARCH = "search"
    
    # Operation types
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    EXPORT = "export"
    IMPORT = "import"
    
    # Special tags
    BULK = "bulk"
    BACKUP = "backup"
    METRICS = "metrics"
    COVER_LETTER = "cover-letter"
    
    @classmethod
    def for_experience_tool(cls, section: str, operation: str) -> set[str]:
        """Get standard tags for an experience tool.
        
        Args:
            section: One of work, education, skills, projects, basics
            operation: One of create, read, update, delete
            
        Returns:
            Set of tags
        """
        return {cls.EXPERIENCE, section, operation}
    
    @classmethod
    def for_crud_tool(cls, category: str, operation: str) -> set[str]:
        """Get standard tags for a CRUD tool.
        
        Args:
            category: Tool category (e.g., templates, applications)
            operation: One of create, read, update, delete
            
        Returns:
            Set of tags
        """
        return {category, operation}
