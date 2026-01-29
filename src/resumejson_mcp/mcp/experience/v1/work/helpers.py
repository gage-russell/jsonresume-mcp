"""Helper functions for work MCP tools."""

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Work, MCPBullet, MCPMajorProject, MCPWorkDetails
from resumejson_mcp.lib.pending_actions import (
    get_tracker,
    ActionType,
    ActionPriority,
)
from resumejson_mcp.mcp.experience.shared_helpers import (
    ensure_mcp_id,
    ensure_nested_ids,
)


def ensure_work_ids(work: Work) -> None:
    """Ensure work and all nested items have IDs."""
    # Ensure main mcp_details.id
    ensure_mcp_id(work, MCPWorkDetails)
    
    # Ensure nested IDs for bullets and major projects
    ensure_nested_ids(work.mcp_details.bullets)
    ensure_nested_ids(work.mcp_details.major_projects)


def format_bullets(bullets: list[MCPBullet]) -> str:
    """Format bullets for display."""
    if not bullets:
        return "  • No bullets captured yet"
    
    return "\n".join(
        f"  • {bullet.text}{f' [{', '.join(bullet.tags)}]' if bullet.tags else ''}"
        for bullet in bullets
    )


def format_major_projects(projects: list[MCPMajorProject]) -> str:
    """Format major projects for display.
    
    Note: These are work[].major_projects - contextual information about projects
    done at this job. They help the AI understand your work to generate tailored bullets.
    They are NOT the same as top-level 'projects' which are portfolio pieces that
    appear directly on resumes.
    """
    if not projects:
        return "  → No major projects captured yet"
    
    def format_project(project: MCPMajorProject) -> list[str]:
        tech_str = f" [{', '.join(project.technologies)}]" if project.technologies else ""
        result = [f"  → {project.name}{tech_str}"]
        if project.summary:
            summary = project.summary[:100] + ("..." if len(project.summary) > 100 else "")
            result.append(f"    {summary}")
        if project.outcomes:
            result.append(f"    📊 {project.outcomes}")
        return result
    
    return "\n".join(line for project in projects for line in format_project(project))


def extract_technologies(work: Work) -> list[str]:
    """Extract unique technologies from major projects."""
    if not work.mcp_details:
        return []
    
    tech_set = set()
    for project in work.mcp_details.major_projects:
        if project.technologies:
            tech_set.update(project.technologies)
    
    return sorted(tech_set)


def detect_missing_info(work: Work) -> list[str]:
    """Identify missing or incomplete information."""
    missing = []
    
    # Check standard JSON Resume fields
    if not work.summary:
        missing.append("No summary - add a brief overview of the role")
    
    if not work.highlights:
        missing.append("No highlights - standard JSON Resume accomplishments are empty")
    
    # Check MCP extensions
    if not work.mcp_details:
        missing.append("No MCP details - need bullets and projects for resume generation")
        return missing
    
    if not work.mcp_details.bullets:
        missing.append("No bullets - what were your key accomplishments?")
    
    if not work.mcp_details.major_projects:
        missing.append("No major projects - what specific projects did you work on?")
    else:
        # Check project completeness
        incomplete_projects = [
            p.name for p in work.mcp_details.major_projects
            if not p.outcomes
        ]
        if incomplete_projects:
            missing.append(f"Projects missing outcomes/metrics: {', '.join(incomplete_projects)}")
    
    if not work.mcp_details.tags:
        missing.append("No tags - add relevant keywords for job matching")
    
    return missing


def format_work_result(work: Work, action: str, store: ExperienceStore) -> str:
    """Format a complete work position result with guidance and pending actions.
    
    Args:
        work: The work position to format
        action: "added" or "updated"
        store: ExperienceStore instance for additional queries
    
    Returns:
        Formatted output with position details and pending actions
    """
    tracker = get_tracker()
    work_id = work.mcp_details.id if work.mcp_details else "unknown"
    work_name = f"{work.position} at {work.name}"
    
    # Header
    date_range = f"{work.start_date} - {work.end_date or 'Present'}"
    location_str = f" | {work.location}" if work.location else ""
    url_str = f"\n🔗 {work.url}" if work.url else ""
    
    header = f"""✓ WORK POSITION {action.upper()}

{'=' * 70}
{work.position} at {work.name}
{date_range}{location_str}{url_str}
{'=' * 70}
"""
    
    # Summary
    summary_section = f"\n📝 SUMMARY:\n{work.summary}\n" if work.summary else ""
    
    # Bullets
    bullets_section = ""
    if work.mcp_details:
        bullet_count = len(work.mcp_details.bullets)
        bullets_section = f"\n💼 ACCOMPLISHMENTS ({bullet_count}):\n"
        bullets_section += format_bullets(work.mcp_details.bullets)
    
    # Major Projects
    projects_section = ""
    if work.mcp_details:
        project_count = len(work.mcp_details.major_projects)
        projects_section = f"\n\n🚀 MAJOR PROJECTS ({project_count}):\n"
        projects_section += format_major_projects(work.mcp_details.major_projects)
    
    # =========================================================================
    # PENDING ACTIONS - Track what needs to be done
    # =========================================================================
    
    # 1. Check for missing bullets (CRITICAL)
    if not (work.mcp_details and work.mcp_details.bullets):
        tracker.add_bullets_action(work_id, work_name)
    
    # 2. Check for missing major projects (CRITICAL)
    if not (work.mcp_details and work.mcp_details.major_projects):
        tracker.add_major_project_action(work_id, work_name)
    
    # 3. Extract technologies and check for missing skills (HIGH)
    tech_list = extract_technologies(work)
    all_skills = store.get_all_skills()
    
    # Check against skill keywords, not just skill names (categories)
    existing_keywords = set()
    for skill in all_skills:
        existing_keywords.update(kw.lower() for kw in skill.keywords)
        if skill.name:
            existing_keywords.add(skill.name.lower())
    
    missing_skills = [t for t in tech_list if t.lower() not in existing_keywords]
    
    tech_section = ""
    if tech_list:
        tech_section = f"""

⚙️  TECHNOLOGIES MENTIONED:
{', '.join(tech_list)}"""
        
        if missing_skills:
            # Add to tracker
            tracker.add_skills_action(missing_skills, work_id, work_name)
            tech_section += f"""

📌 SKILLS TO ADD: {', '.join(missing_skills)}"""
    
    # 4. Check for portfolio project candidates (MEDIUM)
    portfolio_candidates = []
    if work.mcp_details and work.mcp_details.major_projects:
        for project in work.mcp_details.major_projects:
            summary_lower = (project.summary or '').lower()
            name_lower = (project.name or '').lower()
            
            # Indicators this might be a portfolio project
            indicators = ['github', 'open source', 'published', 'app store', 'side project', 'personal project']
            if any(keyword in summary_lower or keyword in name_lower for keyword in indicators):
                portfolio_candidates.append(project.name)
    
    if portfolio_candidates:
        tracker.add_portfolio_project_action(portfolio_candidates, work_id)
    
    # Missing information summary
    missing = detect_missing_info(work)
    missing_section = ""
    if missing:
        missing_section = f"""

⚠️  INCOMPLETE:
{chr(10).join(f'  • {m}' for m in missing)}"""
    
    # Format pending actions from tracker
    pending_section = tracker.format_summary()
    
    return header + summary_section + bullets_section + projects_section + tech_section + missing_section + "\n\n" + pending_section
