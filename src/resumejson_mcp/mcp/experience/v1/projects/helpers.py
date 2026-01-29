"""Helper functions for project MCP tools."""

from resumejson_mcp.lib.experience.models import Project, MCPProjectDetails
from resumejson_mcp.mcp.experience.shared_helpers import ensure_mcp_id


def ensure_project_ids(project: Project) -> None:
    """Ensure project has all required IDs set."""
    ensure_mcp_id(project, MCPProjectDetails)


def detect_missing_info(project: Project) -> list[str]:
    """Identify missing or incomplete information in a project."""
    missing = []
    
    if not project.description:
        missing.append("No description - add a brief summary of the project")
    
    if not project.highlights:
        missing.append("No highlights - list 3-5 key features or accomplishments")
    
    if not project.keywords:
        missing.append("No keywords - specify technologies/tools used")
    
    if not project.url:
        missing.append("No URL - add a link to GitHub, demo, or documentation")
    
    if not project.mcp_details:
        missing.append("No MCP details - need one-liner and tags")
    elif not project.mcp_details.one_liner:
        missing.append("No one-liner - add a brief description for tight layouts")
    
    return missing


def format_project_result(project: Project, action: str) -> str:
    """Format a project result for display to the agent."""
    # Header
    header = f"✓ PROJECT {action.upper()}\n" + "=" * 60 + "\n"
    
    # Basic info
    date_range = ""
    if project.start_date or project.end_date:
        start = project.start_date or "?"
        end = project.end_date or "Present"
        date_range = f" ({start} - {end})"
    
    basic_info = f"""\n{project.name}{date_range}
ID: {project.mcp_details.id if project.mcp_details else 'N/A'}
{project.description or '(No description)'}
"""
    
    if project.url:
        basic_info += f"URL: {project.url}\n"
    if project.entity:
        basic_info += f"Entity: {project.entity}\n"
    if project.type:
        basic_info += f"Type: {project.type}\n"
    if project.roles:
        basic_info += f"Roles: {', '.join(project.roles)}\n"
    if project.mcp_details and project.mcp_details.one_liner:
        basic_info += f"One-liner: {project.mcp_details.one_liner}\n"
    
    # Keywords section
    keywords_section = ""
    if project.keywords:
        keywords_section = f"""\n⚙️  KEYWORDS ({len(project.keywords)}):
{', '.join(project.keywords)}
"""
    
    # Highlights section
    highlights_section = ""
    if project.highlights:
        highlights_section = f"""\n✨ HIGHLIGHTS ({len(project.highlights)}):\n"""
        highlights_section += "\n".join(f"  • {h}" for h in project.highlights) + "\n"
    
    # Tags section
    tags_section = ""
    if project.mcp_details and project.mcp_details.tags:
        tags_section = f"""\n🏷️  TAGS:
{', '.join(project.mcp_details.tags)}
"""
    
    # Missing information
    missing = detect_missing_info(project)
    missing_section = ""
    if missing:
        missing_section = f"""\n⚠️  MISSING/INCOMPLETE INFORMATION:
{chr(10).join(f'  • {m}' for m in missing)}

⚠️  IMPORTANT: Ask targeted follow-up questions to complete this information.
"""
    
    # Next steps guidance
    next_steps = f"""\n🎯 NEXT STEPS (REQUIRED):
1. Show user the captured information above
2. Ask: "Does this look correct for your {project.name} project?"
"""
    
    if missing:
        next_steps += f"""3. ⚠️  CRITICAL: This project is missing important information.
   Ask specific follow-up questions to complete it.
4. Update the project once you have more information
"""
    else:
        next_steps += f"""3. ✓ This project looks complete!
"""
    
    final_step = 5 if missing else 4
    next_steps += f"""{final_step}. Ask: "Would you like to add another project, or move on to work experience or skills?"

💡 REMINDER: Top-level projects are portfolio/showcase projects that appear directly on resumes.
   These are different from work[].major_projects which provide context for generating bullets."""
    
    return header + basic_info + keywords_section + highlights_section + tags_section + missing_section + next_steps
