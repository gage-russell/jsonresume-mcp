"""Models for pending actions tracking."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class ActionPriority(str, Enum):
    """Priority levels for pending actions."""
    CRITICAL = "critical"  # Must complete before moving on
    HIGH = "high"          # Should complete soon
    MEDIUM = "medium"      # Can defer but shouldn't forget
    LOW = "low"            # Nice to have


class ActionType(str, Enum):
    """Types of pending actions."""
    ADD_SKILLS = "add_skills"
    ADD_MAJOR_PROJECT = "add_major_project"
    ADD_BULLETS = "add_bullets"
    ADD_PROJECT = "add_project"  # Portfolio project
    CONFIRM_WITH_USER = "confirm_with_user"
    EXTRACT_MORE_INFO = "extract_more_info"
    UPDATE_WORK = "update_work"
    DELETE_DUPLICATE = "delete_duplicate"


class PendingAction(BaseModel):
    """A pending action that the LLM should complete."""
    
    id: str = Field(..., description="Unique identifier for this action")
    action_type: ActionType = Field(..., description="Type of action to take")
    priority: ActionPriority = Field(..., description="Priority level")
    description: str = Field(..., description="Human-readable description of what to do")
    
    # Context for the action
    target_id: str | None = Field(None, description="ID of the entity to act on (work_id, skill_id, etc.)")
    target_name: str | None = Field(None, description="Human-readable name of the target")
    items: list[str] = Field(default_factory=list, description="List of items (skills to add, projects to create, etc.)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.now)
    completed: bool = Field(default=False)
    completed_at: datetime | None = None
    
    def mark_completed(self) -> None:
        """Mark this action as completed."""
        self.completed = True
        self.completed_at = datetime.now()
    
    def to_instruction(self) -> str:
        """Convert to a human-readable instruction."""
        if self.action_type == ActionType.ADD_SKILLS:
            return f"[{self.priority.value.upper()}] Add skills: {', '.join(self.items[:5])}" + (
                f" (+{len(self.items) - 5} more)" if len(self.items) > 5 else ""
            )
        elif self.action_type == ActionType.ADD_MAJOR_PROJECT:
            return f"[{self.priority.value.upper()}] Add major project details to: {self.target_name}"
        elif self.action_type == ActionType.ADD_BULLETS:
            return f"[{self.priority.value.upper()}] Add accomplishment bullets to: {self.target_name}"
        elif self.action_type == ActionType.ADD_PROJECT:
            return f"[{self.priority.value.upper()}] Add portfolio project: {', '.join(self.items)}"
        elif self.action_type == ActionType.CONFIRM_WITH_USER:
            return f"[{self.priority.value.upper()}] Ask user: {self.description}"
        elif self.action_type == ActionType.EXTRACT_MORE_INFO:
            return f"[{self.priority.value.upper()}] Get more info: {self.description}"
        elif self.action_type == ActionType.DELETE_DUPLICATE:
            return f"[{self.priority.value.upper()}] Delete duplicate: {self.target_name} (ID: {self.target_id})"
        else:
            return f"[{self.priority.value.upper()}] {self.description}"


class PendingActionsResult(BaseModel):
    """Result container that includes both the result text and pending actions."""
    
    result: str = Field(..., description="The formatted result text to display")
    pending_actions: list[PendingAction] = Field(
        default_factory=list, 
        description="Actions the LLM should take next"
    )
    
    def has_critical_actions(self) -> bool:
        """Check if there are any critical pending actions."""
        return any(a.priority == ActionPriority.CRITICAL and not a.completed for a in self.pending_actions)
    
    def get_incomplete_actions(self) -> list[PendingAction]:
        """Get all incomplete actions sorted by priority."""
        priority_order = {
            ActionPriority.CRITICAL: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3,
        }
        return sorted(
            [a for a in self.pending_actions if not a.completed],
            key=lambda a: priority_order[a.priority]
        )
    
    def format_actions_summary(self) -> str:
        """Format pending actions as a summary string."""
        incomplete = self.get_incomplete_actions()
        if not incomplete:
            return "\n✅ No pending actions - workflow complete!"
        
        lines = [
            "\n" + "=" * 60,
            "📋 PENDING ACTIONS (DO NOT SKIP):",
            "=" * 60,
            *[f"{i}. {action.to_instruction()}" for i, action in enumerate(incomplete, 1)],
            "",
            "⚠️  Complete these actions before moving on.",
            "Use get_pending_todos to check remaining actions.",
        ]
        
        return "\n".join(lines)
    
    def to_output(self) -> str:
        """Combine result and actions summary for tool output."""
        return self.result + self.format_actions_summary()
