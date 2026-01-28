"""Pending actions tracker - singleton for managing workflow state."""

from typing import Optional
from uuid import uuid4

from resumejson_mcp.lib.pending_actions.models import (
    PendingAction,
    ActionType,
    ActionPriority,
)


class PendingActionsTracker:
    """Singleton tracker for pending actions across the session.
    
    This helps ensure the LLM completes required workflow steps.
    """
    
    _instance: Optional["PendingActionsTracker"] = None
    _actions: list[PendingAction]
    
    def __new__(cls) -> "PendingActionsTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = []
        return cls._instance
    
    def add_action(
        self,
        action_type: ActionType,
        priority: ActionPriority,
        description: str,
        target_id: str | None = None,
        target_name: str | None = None,
        items: list[str] | None = None,
        metadata: dict | None = None,
    ) -> PendingAction:
        """Add a new pending action."""
        action = PendingAction(
            id=str(uuid4()),
            action_type=action_type,
            priority=priority,
            description=description,
            target_id=target_id,
            target_name=target_name,
            items=items or [],
            metadata=metadata or {},
        )
        self._actions.append(action)
        return action
    
    def add_skills_action(
        self,
        skills: list[str],
        source_work_id: str | None = None,
        source_work_name: str | None = None,
    ) -> PendingAction:
        """Convenience method to add a skills action."""
        return self.add_action(
            action_type=ActionType.ADD_SKILLS,
            priority=ActionPriority.HIGH,
            description=f"Add {len(skills)} skills extracted from work experience",
            target_id=source_work_id,
            target_name=source_work_name,
            items=skills,
        )
    
    def add_major_project_action(
        self,
        work_id: str,
        work_name: str,
    ) -> PendingAction:
        """Add action to create major project details."""
        return self.add_action(
            action_type=ActionType.ADD_MAJOR_PROJECT,
            priority=ActionPriority.CRITICAL,
            description=f"Add major project details to {work_name}",
            target_id=work_id,
            target_name=work_name,
        )
    
    def add_bullets_action(
        self,
        work_id: str,
        work_name: str,
    ) -> PendingAction:
        """Add action to add bullets to a work position."""
        return self.add_action(
            action_type=ActionType.ADD_BULLETS,
            priority=ActionPriority.CRITICAL,
            description=f"Add accomplishment bullets to {work_name}",
            target_id=work_id,
            target_name=work_name,
        )
    
    def add_portfolio_project_action(
        self,
        project_names: list[str],
        source_work_id: str | None = None,
    ) -> PendingAction:
        """Add action to create portfolio project(s)."""
        return self.add_action(
            action_type=ActionType.ADD_PROJECT,
            priority=ActionPriority.MEDIUM,
            description=f"Add {len(project_names)} portfolio project(s)",
            target_id=source_work_id,
            items=project_names,
        )
    
    def add_confirm_action(
        self,
        message: str,
        metadata: dict | None = None,
    ) -> PendingAction:
        """Add action to confirm something with user."""
        return self.add_action(
            action_type=ActionType.CONFIRM_WITH_USER,
            priority=ActionPriority.MEDIUM,
            description=message,
            metadata=metadata or {},
        )
    
    def add_delete_duplicate_action(
        self,
        duplicate_id: str,
        duplicate_name: str,
    ) -> PendingAction:
        """Add action to delete a duplicate entry."""
        return self.add_action(
            action_type=ActionType.DELETE_DUPLICATE,
            priority=ActionPriority.LOW,
            description=f"Delete duplicate entry: {duplicate_name}",
            target_id=duplicate_id,
            target_name=duplicate_name,
        )
    
    def get_action(self, action_id: str) -> PendingAction | None:
        """Get a specific action by ID."""
        for action in self._actions:
            if action.id == action_id:
                return action
        return None
    
    def complete_action(self, action_id: str) -> bool:
        """Mark an action as completed."""
        action = self.get_action(action_id)
        if action:
            action.mark_completed()
            return True
        return False
    
    def complete_actions_of_type(
        self,
        action_type: ActionType,
        target_id: str | None = None,
    ) -> int:
        """Complete all actions of a given type (optionally filtered by target)."""
        completed_count = 0
        for action in self._actions:
            if action.action_type == action_type and not action.completed:
                if target_id is None or action.target_id == target_id:
                    action.mark_completed()
                    completed_count += 1
        return completed_count
    
    def get_incomplete_actions(self) -> list[PendingAction]:
        """Get all incomplete actions sorted by priority."""
        priority_order = {
            ActionPriority.CRITICAL: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3,
        }
        return sorted(
            [a for a in self._actions if not a.completed],
            key=lambda a: priority_order[a.priority]
        )
    
    def get_critical_actions(self) -> list[PendingAction]:
        """Get all incomplete critical actions."""
        return [
            a for a in self._actions 
            if not a.completed and a.priority == ActionPriority.CRITICAL
        ]
    
    def has_critical_actions(self) -> bool:
        """Check if there are any incomplete critical actions."""
        return len(self.get_critical_actions()) > 0
    
    def clear_completed(self) -> int:
        """Remove all completed actions. Returns count removed."""
        before = len(self._actions)
        self._actions = [a for a in self._actions if not a.completed]
        return before - len(self._actions)
    
    def clear_all(self) -> int:
        """Clear all actions. Returns count removed."""
        count = len(self._actions)
        self._actions = []
        return count
    
    def format_summary(self) -> str:
        """Format all incomplete actions as a summary string."""
        incomplete = self.get_incomplete_actions()
        
        if not incomplete:
            return "✅ No pending actions - all tasks complete!"
        
        lines = [
            "📋 PENDING ACTIONS",
            "=" * 60,
        ]
        
        # Group by priority
        for priority in [ActionPriority.CRITICAL, ActionPriority.HIGH, ActionPriority.MEDIUM, ActionPriority.LOW]:
            priority_actions = [a for a in incomplete if a.priority == priority]
            if priority_actions:
                emoji = {
                    ActionPriority.CRITICAL: "🔴",
                    ActionPriority.HIGH: "🟠",
                    ActionPriority.MEDIUM: "🟡",
                    ActionPriority.LOW: "🟢",
                }[priority]
                lines.append(f"\n{emoji} {priority.value.upper()}:")
                for action in priority_actions:
                    lines.append(f"  • {action.to_instruction()}")
                    if action.items:
                        items_preview = ", ".join(action.items[:3])
                        if len(action.items) > 3:
                            items_preview += f" (+{len(action.items) - 3} more)"
                        lines.append(f"    Items: {items_preview}")
        
        lines.append("")
        lines.append(f"Total: {len(incomplete)} pending action(s)")
        
        if self.has_critical_actions():
            lines.append("")
            lines.append("⚠️  CRITICAL actions must be completed before proceeding!")
        
        return "\n".join(lines)
    
    def format_compact(self) -> str:
        """Format a compact one-line summary."""
        incomplete = self.get_incomplete_actions()
        if not incomplete:
            return "✅ No pending actions"
        
        critical = len([a for a in incomplete if a.priority == ActionPriority.CRITICAL])
        high = len([a for a in incomplete if a.priority == ActionPriority.HIGH])
        other = len(incomplete) - critical - high
        
        parts = []
        if critical:
            parts.append(f"🔴 {critical} critical")
        if high:
            parts.append(f"🟠 {high} high")
        if other:
            parts.append(f"🟡 {other} other")
        
        return f"📋 Pending: {', '.join(parts)}"


# Convenience function to get the tracker
def get_tracker() -> PendingActionsTracker:
    """Get the global pending actions tracker."""
    return PendingActionsTracker()
