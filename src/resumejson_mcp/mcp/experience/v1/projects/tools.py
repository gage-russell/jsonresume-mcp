"""MCP tools for managing portfolio projects."""

from uuid import uuid4

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Project
from resumejson_mcp.mcp.tags import PROJECTS_TAGS, CREATE, READ, UPDATE, DELETE, BULK
from resumejson_mcp.mcp.experience.shared_helpers import handle_id_collision
from resumejson_mcp.mcp.experience.v1.projects.helpers import (
    format_project_result,
    ensure_project_ids,
)


@tool(
    name="get_all_projects",
    tags=PROJECTS_TAGS | {"read"},
    description="""Get all portfolio projects from experience store.
    
    Portfolio projects are showcased work that appears directly on resumes.
    These are different from work[].major_projects which are contextual information
    used to generate tailored resume bullets."""
)
def get_all_projects() -> str:
    store = ExperienceStore()
    projects = store.get_all_projects()
    
    if not projects:
        return """No projects found in experience store.

📝 ABOUT PROJECTS:
Portfolio projects are showcase work that appears directly on resumes (GitHub repos,
side projects, open source contributions, etc.).

This is different from work[].major_projects which provide context for generating
targeted resume bullets from work experience.

NEXT STEPS:
Ask the user: "Do you have any portfolio projects you'd like to showcase? 
For example: open source contributions, side projects, or personal websites?"
"""
    
    # Format summary
    lines = ["🚀 PORTFOLIO PROJECTS\n" + "=" * 60]
    for project in projects:
        date_info = ""
        if project.start_date or project.end_date:
            date_info = f" ({project.start_date or '?'} - {project.end_date or 'Present'})"
        
        highlight_count = len(project.highlights)
        keyword_count = len(project.keywords)
        
        lines.append(f"\n{project.name}{date_info}")
        if project.description:
            lines.append(f"  {project.description}")
        lines.append(f"  • {highlight_count} highlight(s), {keyword_count} keyword(s)")
        if project.url:
            lines.append(f"  • URL: {project.url}")
        lines.append(f"  ID: {project.mcp_details.id if project.mcp_details else 'N/A'}")
    
    result = "\n".join(lines)
    result += "\n\nNEXT STEPS:\nTo view details of a specific project, use get_project_by_id."
    result += "\nTo add a new project, use add_project."
    
    return result


@tool(
    name="get_project_by_id",
    tags=PROJECTS_TAGS | {"read"},
    description="""Get a specific portfolio project by its mcp-details.id.
    
    Args:
        mcp_id: The mcp-details.id of the project"""
)
def get_project_by_id(mcp_id: str) -> str:
    store = ExperienceStore()
    
    try:
        project = store.get_project_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Project with ID {mcp_id} not found.

RECOVERY:
Use get_all_projects to see existing projects and their IDs."""
    
    return format_project_result(project, action="retrieved")


@tool(
    name="add_project",
    tags=PROJECTS_TAGS | {"create"},
    description="""Add a new portfolio project.
    
    Portfolio projects are showcase work that appears directly on resumes
    (e.g., GitHub repos, side projects, open source contributions).
    
    These are DIFFERENT from work[].major_projects which are contextual information
    about projects done at jobs. Those major_projects help the AI generate tailored
    resume bullets but don't appear directly on resumes.
    
    Required fields:
    - name: Clear project title
    - description: Brief summary (2-3 sentences)
    - highlights: List of key accomplishments or features (3-5 recommended)
    - keywords: Technologies/tools used
    - url: Live demo, GitHub repo, or documentation
    - mcp_details.one_liner: Ultra-brief description for tight layouts
    - mcp_details.tags: For filtering/matching to job descriptions
    
    Args:
        project: Complete Project object"""
)
def add_project(project: Project) -> str:
    store = ExperienceStore()
    
    # Ensure all IDs are set
    ensure_project_ids(project)
    
    # Check for ID collision and regenerate if needed
    handle_id_collision(project, store.get_project_by_id, ensure_project_ids)
    
    store.add_project(project)
    
    return format_project_result(project, action="added")


@tool(
    name="add_projects",
    tags=PROJECTS_TAGS | {"create", "bulk"},
    description="""Add multiple portfolio projects at once.
    
    Use this for bulk adding when the user provides multiple projects.
    
    Args:
        projects: List of Project objects"""
)
def add_projects(projects: list[Project]) -> str:
    store = ExperienceStore()
    
    # Ensure all IDs are set and check for collisions
    for project in projects:
        ensure_project_ids(project)
        handle_id_collision(project, store.get_project_by_id, ensure_project_ids)
    
    store.add_projects(projects)
    
    return f"""✓ {len(projects)} PROJECTS ADDED

Added projects:
{chr(10).join(f'  • {p.name} (ID: {p.mcp_details.id})' for p in projects)}

NEXT STEPS:
Ask user: "I've added those projects. Would you like to add more, or move on to work experience?"
"""


@tool(
    name="update_project",
    tags=PROJECTS_TAGS | {"update"},
    description="""Update an existing portfolio project.
    
    Pass the complete Project object with mcp_details.id matching an existing project.
    
    Args:
        project: Complete Project object with mcp_details.id"""
)
def update_project(project: Project) -> str:
    store = ExperienceStore()
    
    # Verify project exists
    try:
        store.get_project_by_id(project.mcp_details.id)
    except ValueError:
        return f"""✗ ERROR: Project with ID {project.mcp_details.id} not found.

RECOVERY:
- Use get_all_projects to see existing projects and their IDs
- Or use add_project to create a new project instead"""
    
    ensure_project_ids(project)
    store.update_project(project.mcp_details.id, project)
    
    return format_project_result(project, action="updated")


@tool(
    name="delete_project",
    tags=PROJECTS_TAGS | {"delete"},
    description="""Delete a portfolio project by its mcp-details.id.
    
    Args:
        mcp_id: The mcp-details.id of the project to delete"""
)
def delete_project(mcp_id: str) -> str:
    store = ExperienceStore()
    
    # Get project first to show what will be deleted
    try:
        project = store.get_project_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Project with ID {mcp_id} not found.

RECOVERY:
Use get_all_projects to see existing projects and their IDs."""
    
    store.delete_project(mcp_id)
    
    return f"""✓ PROJECT DELETED

Removed: {project.name}
{project.description or '(No description)'}

NEXT STEPS:
Confirm with user: "I've deleted the '{project.name}' project. Is there anything else you'd like to update?"
"""
