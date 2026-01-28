"""MCP tools for workflow and pending actions management."""

from fastmcp.tools import tool

from resumejson_mcp.lib.pending_actions import get_tracker, ActionType


@tool(
    name="get_pending_todos",
    description="""Get all pending actions that need to be completed.
    
    IMPORTANT: Call this tool frequently to check if you have pending work to complete.
    Pending actions are created automatically when you:
    - Add work positions (missing skills, projects, bullets are tracked)
    - Perform operations that require follow-up
    
    Priority levels:
    - CRITICAL: Must complete before moving on (e.g., missing bullets/projects)
    - HIGH: Should complete soon (e.g., adding extracted skills)
    - MEDIUM: Can defer but shouldn't forget (e.g., portfolio projects)
    - LOW: Nice to have
    
    Returns:
        Summary of all pending actions grouped by priority"""
)
def get_pending_todos() -> str:
    tracker = get_tracker()
    
    incomplete = tracker.get_incomplete_actions()
    
    if not incomplete:
        return """✅ NO PENDING ACTIONS

All tasks are complete! You can:
- Add more work experience with add_work
- Generate a tailored resume for a job
- Ask the user what they'd like to do next"""
    
    result = tracker.format_summary()
    
    # Add guidance on how to complete each type
    result += """

📖 HOW TO COMPLETE ACTIONS:

🔴 CRITICAL - add_bullets / add_major_project:
   Use add_bullet_to_work(work_id, bullet) or add_major_project_to_work(work_id, project)
   Ask user for accomplishments and project details if needed

🟠 HIGH - add_skills:
   Use add_skills(skills) to add skill categories with keywords
   Group extracted technologies into logical categories (Languages, Frameworks, Tools, etc.)

🟡 MEDIUM - add_project (portfolio):
   Ask user if they want to showcase these as portfolio projects
   If yes, use add_project(project) to create top-level portfolio entry

🟢 LOW - cleanup:
   Can be deferred, complete when convenient

Use complete_todo(action_id) to mark an action as done after completing it."""
    
    return result


@tool(
    name="complete_todo",
    description="""Mark a pending action as completed.
    
    Call this after you've completed an action to remove it from the pending list.
    
    Args:
        action_id: The ID of the action to mark complete
        
    Returns:
        Confirmation and remaining pending actions count"""
)
def complete_todo(action_id: str) -> str:
    tracker = get_tracker()
    
    action = tracker.get_action(action_id)
    if not action:
        return f"""❌ Action not found: {action_id}

Use get_pending_todos to see current pending actions and their IDs."""
    
    if action.completed:
        return f"""⚠️ Action already completed: {action.description}"""
    
    action.mark_completed()
    
    remaining = tracker.get_incomplete_actions()
    
    return f"""✓ COMPLETED: {action.description}

{tracker.format_compact()}"""


@tool(
    name="complete_todos_of_type",
    description="""Mark all pending actions of a specific type as completed.
    
    Useful when you've completed a batch of related actions (e.g., added all missing skills).
    
    Args:
        action_type: One of: add_skills, add_major_project, add_bullets, add_project, 
                     confirm_with_user, extract_more_info, update_work, delete_duplicate
        target_id: Optional - only complete actions for this specific target (work_id, etc.)
        
    Returns:
        Count of actions completed and remaining pending actions"""
)
def complete_todos_of_type(action_type: str, target_id: str | None = None) -> str:
    tracker = get_tracker()
    
    # Map string to enum
    type_map = {
        "add_skills": ActionType.ADD_SKILLS,
        "add_major_project": ActionType.ADD_MAJOR_PROJECT,
        "add_bullets": ActionType.ADD_BULLETS,
        "add_project": ActionType.ADD_PROJECT,
        "confirm_with_user": ActionType.CONFIRM_WITH_USER,
        "extract_more_info": ActionType.EXTRACT_MORE_INFO,
        "update_work": ActionType.UPDATE_WORK,
        "delete_duplicate": ActionType.DELETE_DUPLICATE,
    }
    
    if action_type not in type_map:
        return f"""❌ Invalid action_type: {action_type}

Valid types: {', '.join(type_map.keys())}"""
    
    completed_count = tracker.complete_actions_of_type(type_map[action_type], target_id)
    
    if completed_count == 0:
        return f"""⚠️ No pending actions of type '{action_type}' found."""
    
    return f"""✓ COMPLETED {completed_count} action(s) of type '{action_type}'

{tracker.format_compact()}"""


@tool(
    name="clear_completed_todos",
    description="""Remove all completed actions from the tracker.
    
    Use this to clean up the action list after a batch of work.
    
    Returns:
        Count of actions cleared"""
)
def clear_completed_todos() -> str:
    tracker = get_tracker()
    
    cleared = tracker.clear_completed()
    remaining = len(tracker.get_incomplete_actions())
    
    return f"""✓ Cleared {cleared} completed action(s)
📋 {remaining} action(s) still pending

{tracker.format_compact()}"""
