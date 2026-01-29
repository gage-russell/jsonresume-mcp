"""MCP tools for managing work experience."""

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Work, MCPBullet, MCPMajorProject
from resumejson_mcp.lib.pending_actions import get_tracker, ActionType
from resumejson_mcp.mcp.experience.shared_helpers import handle_id_collision
from resumejson_mcp.mcp.tags import WORK_TAGS, CREATE, READ, UPDATE, DELETE, BULK
from resumejson_mcp.mcp.experience.v1.work.helpers import (
    format_work_result,
    ensure_work_ids,
)


@tool(
    name="get_all_work",
    tags=WORK_TAGS | {"read", "list"},
    description="""Get all work positions from experience store.
    
    Returns a formatted list of all work positions with their details.
    Use this to see what experience is already captured.
    
    When reviewing positions, check if bullets and major projects are populated.
    If any position is missing these, you should proactively ask the user for more details."""
)
def get_all_work() -> str:
    store = ExperienceStore()
    work_list = store.get_all_work()
    
    if not work_list:
        return """No work positions found in experience store.

NEXT STEPS:
Ask the user: "Let's add your work experience. What's the most recent role you'd like to add?"
Then use add_work to capture the position."""
    
    # Format summary
    lines = ["📋 WORK EXPERIENCE\n" + "=" * 60]
    for work in work_list:
        date_range = f"{work.start_date} - {work.end_date or 'Present'}"
        bullet_count = len(work.mcp_details.bullets) if work.mcp_details else 0
        project_count = len(work.mcp_details.major_projects) if work.mcp_details else 0
        
        lines.append(f"\n{work.position} at {work.name}")
        lines.append(f"  {date_range}")
        lines.append(f"  • {bullet_count} bullet(s), {project_count} major project(s)")
        lines.append(f"  ID: {work.mcp_details.id if work.mcp_details else 'N/A'}")
    
    result = "\n".join(lines)
    result += "\n\nNEXT STEPS:\nTo view details of a specific position, ask the user which one and use get_work_by_id."
    result += "\nTo add a new position, use add_work."
    
    return result


@tool(
    name="get_work_by_id",
    tags=WORK_TAGS | {"read"},
    description="""Get a specific work position by its mcp-details.id.
    
    Use this to view full details of a position including all bullets and major projects.
    
    Args:
        mcp_id: The mcp-details.id of the work position"""
)
def get_work_by_id(mcp_id: str) -> str:
    store = ExperienceStore()
    
    try:
        work = store.get_work_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Work position with ID {mcp_id} not found.

RECOVERY:
Use get_all_work to see existing positions and their IDs."""
    
    return format_work_result(work, action="retrieved", store=store)


@tool(
    name="add_work",
    tags=WORK_TAGS | {"create"},
    description="""Add a new work position with all details.
    
    CRITICAL: You must ALWAYS extract and populate bullets and major projects, even if the user
    doesn't explicitly provide them in list form. INFER accomplishments from their description:
    
    - If user says "I worked on the payment system" → Create a major project for "Payment System"
    - If user mentions "improved performance" → Create a bullet about performance improvements
    - If they describe responsibilities → Convert to accomplishment bullets
    - If they mention technologies → Capture in major project technologies array
    
    DO NOT add a work position with empty bullets and major projects. Always ask follow-up
    questions to extract at least 2-3 bullets and 1-2 major projects before calling this tool.
    
    IMPORTANT DISTINCTION:
    - work[].mcp_details.major_projects: Contextual information about projects done at this job.
      These help the AI understand your work deeply to generate tailored resume bullets.
      They are NOT displayed directly on resumes.
    
    - Top-level projects (use add_project): Portfolio/showcase projects that appear directly
      on resumes (e.g., GitHub repos, side projects, open source contributions).
    
    Required fields to populate:
    - Basic info (position, name/company, dates, location, summary, url)
    - mcp_details.bullets: List of accomplishments/responsibilities (REQUIRED - minimum 2)
    - mcp_details.major_projects: Detailed project context (REQUIRED - minimum 1)
    - mcp_details.tags: Keywords for job matching
    
    Args:
        work: Complete Work object with nested bullets and projects"""
)
def add_work(work: Work) -> str:
    store = ExperienceStore()
    
    # Ensure all IDs are set
    ensure_work_ids(work)
    
    # Check for ID collision and regenerate if needed
    handle_id_collision(work, store.get_work_by_id, ensure_work_ids)
    
    store.add_work(work)
    
    return format_work_result(work, action="added", store=store)


@tool(
    name="update_work",
    tags=WORK_TAGS | {"update"},
    description="""Update an existing work position.
    
    Pass the complete Work object with ALL nested data (bullets, major projects).
    This replaces the entire position - any omitted data will be lost.
    
    Args:
        work: Complete Work object with mcp_details.id matching existing position"""
)
def update_work(work: Work) -> str:
    store = ExperienceStore()
    
    # Verify position exists
    try:
        store.get_work_by_id(work.mcp_details.id)
    except ValueError:
        return f"""✗ ERROR: Work position with ID {work.mcp_details.id} not found.

RECOVERY:
- Use get_all_work to see existing positions and their IDs
- Or use add_work to create a new position instead"""
    
    ensure_work_ids(work)
    store.update_work(work.mcp_details.id, work)
    
    return format_work_result(work, action="updated", store=store)


@tool(
    name="delete_work",
    tags=WORK_TAGS | {"delete"},
    description="""Delete a work position by its mcp-details.id.
    
    This permanently removes the position and ALL nested data (bullets, major projects).
    
    Args:
        mcp_id: The mcp-details.id of the work position to delete"""
)
def delete_work(mcp_id: str) -> str:
    store = ExperienceStore()
    
    # Get position first to show what will be deleted
    try:
        work = store.get_work_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Work position with ID {mcp_id} not found.

RECOVERY:
Use get_all_work to see existing positions and their IDs."""
    
    bullet_count = len(work.mcp_details.bullets) if work.mcp_details else 0
    project_count = len(work.mcp_details.major_projects) if work.mcp_details else 0
    
    store.delete_work(mcp_id)
    
    return f"""✓ WORK POSITION DELETED

Removed: {work.position} at {work.name}
  • {bullet_count} bullet(s) removed
  • {project_count} major project(s) removed

NEXT STEPS:
Confirm with user: "I've deleted your {work.position} role at {work.name}. Is there anything else you'd like to update?"
"""


@tool(
    name="add_bullet_to_work",
    tags=WORK_TAGS | {"update", "bullets"},
    description="""Add a single bullet point to an existing work position.
    
    Use this for incremental updates when user provides additional accomplishments.
    For bulk updates, use update_work with all bullets included.
    
    Args:
        work_id: The mcp-details.id of the work position
        bullet: Bullet object with text and optional tags"""
)
def add_bullet_to_work(work_id: str, bullet: MCPBullet) -> str:
    store = ExperienceStore()
    tracker = get_tracker()
    
    try:
        work = store.get_work_by_id(work_id)
    except ValueError:
        return f"✗ ERROR: Work position with ID {work_id} not found."
    
    added = store.add_bullet_to_work(work_id, bullet)
    new_count = len(work.mcp_details.bullets) + 1 if work.mcp_details else 1
    
    # Auto-complete pending add_bullets action for this work position
    completed = tracker.complete_actions_of_type(ActionType.ADD_BULLETS, work_id)
    
    result = f"""✓ BULLET ADDED

Position: {work.position} at {work.name}
Added: "{added.text}"
Total bullets: {new_count}
"""
    
    if completed > 0:
        result += f"\n✓ Completed pending bullets action"
    
    result += f"\n{tracker.format_compact()}"
    
    return result


@tool(
    name="add_bullets_to_work",
    tags=WORK_TAGS | {"update", "bullets", "bulk"},
    description="""Add multiple bullet points to an existing work position at once.
    
    This is more efficient than calling add_bullet_to_work multiple times
    when you have several accomplishments to add.
    
    Args:
        work_id: The mcp-details.id of the work position
        bullets: List of Bullet objects with text and optional tags
        
    Example:
        add_bullets_to_work("my-work-id", [
            {"text": "Led team of 5 engineers...", "tags": ["leadership", "team"]},
            {"text": "Reduced latency by 40%...", "tags": ["performance", "optimization"]},
            {"text": "Built CI/CD pipeline...", "tags": ["devops", "automation"]}
        ])"""
)
def add_bullets_to_work(work_id: str, bullets: list[MCPBullet]) -> str:
    store = ExperienceStore()
    tracker = get_tracker()
    
    if not bullets:
        return "❌ No bullets provided to add."
    
    try:
        work = store.get_work_by_id(work_id)
    except ValueError:
        return f"✗ ERROR: Work position with ID {work_id} not found.\n\nUse get_all_work to see existing positions and their IDs."
    
    # Add each bullet
    added_count = 0
    for bullet in bullets:
        # Ensure bullet has an ID
        if not bullet.id:
            bullet.id = str(uuid4())
        store.add_bullet_to_work(work_id, bullet)
        added_count += 1
    
    # Reload to get updated count
    work = store.get_work_by_id(work_id)
    new_count = len(work.mcp_details.bullets) if work.mcp_details else 0
    
    # Auto-complete pending add_bullets action for this work position
    completed = tracker.complete_actions_of_type(ActionType.ADD_BULLETS, work_id)
    
    result = f"""✓ {added_count} BULLETS ADDED

Position: {work.position} at {work.name}
Total bullets: {new_count}

Added:
"""
    for bullet in bullets:
        result += f"  • {bullet.text[:70]}{'...' if len(bullet.text) > 70 else ''}\n"
    
    if completed > 0:
        result += f"\n✓ Completed pending bullets action"
    
    result += f"\n{tracker.format_compact()}"
    
    return result


@tool(
    name="add_major_project_to_work",
    tags=WORK_TAGS | {"update", "projects"},
    description="""Add a major project to an existing work position.
    
    IMPORTANT: work[].major_projects are contextual information about projects done at this job.
    They help the AI understand your work deeply to generate tailored resume bullets.
    They are NOT displayed directly on resumes.
    
    For portfolio/showcase projects that appear directly on resumes (GitHub repos, side projects),
    use add_project instead.
    
    Capture detailed project context for resume generation:
    - name: Project name/title
    - summary: What it was and your role
    - technologies: List of tech/tools used
    - outcomes: Results, metrics, impact
    - challenges: Problems solved
    - team_context: Team size, collaboration details
    - tags: For job matching
    
    Args:
        work_id: The mcp-details.id of the work position
        project: Complete MCPMajorProject object"""
)
def add_major_project_to_work(work_id: str, project: MCPMajorProject) -> str:
    store = ExperienceStore()
    tracker = get_tracker()
    
    try:
        work = store.get_work_by_id(work_id)
    except ValueError:
        return f"✗ ERROR: Work position with ID {work_id} not found."
    
    added = store.add_major_project_to_work(work_id, project)
    new_count = len(work.mcp_details.major_projects) + 1 if work.mcp_details else 1
    
    tech_list = project.technologies or []
    
    # Auto-complete pending add_major_project action for this work position
    completed = tracker.complete_actions_of_type(ActionType.ADD_MAJOR_PROJECT, work_id)
    
    result = f"""✓ MAJOR PROJECT ADDED

Position: {work.position} at {work.name}
Project: {added.name}
Technologies: {', '.join(tech_list) if tech_list else 'None specified'}
Total projects: {new_count}
"""
    
    if completed > 0:
        result += f"\n✓ Completed pending major project action"
    
    # Suggest adding technologies as skills (and add pending action)
    if tech_list:
        result += f"""
SKILLS SUGGESTION:
These technologies were mentioned: {', '.join(tech_list)}
Consider adding them as skills if not already present.
"""
        # Check if we already have a skills action, if not add one
        existing_skill_actions = [a for a in tracker.get_incomplete_actions() 
                                  if a.action_type == ActionType.ADD_SKILLS]
        if not existing_skill_actions:
            tracker.add_skills_action(
                skills=tech_list,
                source_work_id=work_id,
                source_work_name=f"{work.position} at {work.name}",
            )
    
    result += f"\n{tracker.format_compact()}"
    
    return result
