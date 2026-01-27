"""Helper functions for work MCP tools."""

from uuid import uuid4

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Work, MCPBullet, MCPMajorProject


def ensure_work_ids(work: Work) -> None:
    """Ensure work and all nested items have IDs."""
    # Ensure main mcp_details.id
    if not work.mcp_details:
        from resumejson_mcp.lib.experience.models import MCPWorkDetails
        work.mcp_details = MCPWorkDetails(id=str(uuid4()))
    elif not work.mcp_details.id:
        work.mcp_details.id = str(uuid4())
    
    # Ensure bullet IDs
    for bullet in work.mcp_details.bullets:
        if not bullet.id:
            bullet.id = str(uuid4())
    
    # Ensure major project IDs
    for project in work.mcp_details.major_projects:
        if not project.id:
            project.id = str(uuid4())


def format_bullets(bullets: list[MCPBullet]) -> str:
    """Format bullets for display."""
    if not bullets:
        return "  • No bullets captured yet"
    
    lines = []
    for bullet in bullets:
        tags_str = f" [{', '.join(bullet.tags)}]" if bullet.tags else ""
        lines.append(f"  • {bullet.text}{tags_str}")
    
    return "\n".join(lines)


def format_major_projects(projects: list[MCPMajorProject]) -> str:
    """Format major projects for display.
    
    Note: These are work[].major_projects - contextual information about projects
    done at this job. They help the AI understand your work to generate tailored bullets.
    They are NOT the same as top-level 'projects' which are portfolio pieces that
    appear directly on resumes.
    """
    if not projects:
        return "  → No major projects captured yet"
    
    lines = []
    for project in projects:
        tech_str = f" [{', '.join(project.technologies)}]" if project.technologies else ""
        lines.append(f"  → {project.name}{tech_str}")
        
        if project.summary:
            summary = project.summary[:100] + ("..." if len(project.summary) > 100 else "")
            lines.append(f"    {summary}")
        
        if project.outcomes:
            lines.append(f"    📊 {project.outcomes}")
    
    return "\n".join(lines)


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
    """Format a complete work position result with guidance.
    
    Args:
        work: The work position to format
        action: "added" or "updated"
        store: ExperienceStore instance for additional queries
    
    Returns:
        Formatted output with position details and next steps
    """
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
    
    # Basic info
    basic_info = ""
    
    # Summary
    summary_section = ""
    if work.summary:
        summary_section = f"\n📝 SUMMARY:\n{work.summary}\n"
    
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
    
    # Extract technologies
    tech_list = extract_technologies(work)
    all_skills = store.get_all_skills()
    skill_names = {s.name for s in all_skills}
    missing_skills = [t for t in tech_list if t not in skill_names]
    
    tech_section = ""
    if tech_list and missing_skills:
        tech_section = f"""

⚙️  TECHNOLOGIES MENTIONED:
{', '.join(tech_list)}

📌 ACTION REQUIRED - AUTOMATICALLY ADD THESE SKILLS:
These technologies aren't in your skills yet: {', '.join(missing_skills)}
CALL add_skills tool NOW to add them automatically.
Do NOT ask permission - add them immediately after showing this output."""
    
    # Missing information
    missing = detect_missing_info(work)
    missing_section = ""
    if missing:
        missing_section = f"""

⚠️  MISSING/INCOMPLETE INFORMATION:
{chr(10).join(f'  • {m}' for m in missing)}

⚠️  IMPORTANT: Ask targeted follow-up questions to extract this information:
  → For bullets: "What were your key accomplishments in this role?"
  → For projects: "What specific projects did you work on? What technologies?"
  → For outcomes: "What were the results? Any metrics or impact you can quantify?"
"""
    
    # Next steps guidance
    has_no_bullets = not work.mcp_details or not work.mcp_details.bullets
    has_no_projects = not work.mcp_details or not work.mcp_details.major_projects
    
    next_steps = f"""

🎯 NEXT STEPS (REQUIRED):
1. Show user the captured information above
2. Ask: "Does this look correct for your {work.position} role at {work.name}?"
"""
    
    if has_no_bullets or has_no_projects:
        critical_items = []
        if has_no_bullets:
            critical_items.append("bullets/accomplishments")
        if has_no_projects:
            critical_items.append("major projects")
        
        next_steps += f"""3. ⚠️  CRITICAL: This position is missing {' and '.join(critical_items)}.
   You MUST ask follow-up questions to extract this information:
   - "What were your main responsibilities and accomplishments?"
   - "What specific projects or initiatives did you work on?"
   - "What technologies, tools, or methodologies did you use?"
   - "What was the impact or outcome of your work? Any metrics?"
4. Use add_bullet_to_work and add_major_project_to_work to populate these
"""
    elif missing:
        next_steps += f"""3. Address incomplete information: "{missing[0]}"
   Ask specific follow-up questions to get the missing details
4. Update the position once you have more information
"""
    else:
        next_steps += f"""3. ✓ This position looks complete with bullets and projects!
"""
    
    # Reuse missing_skills computed earlier in the function
    if missing_skills:
        step_num = 5 if (has_no_bullets or has_no_projects or missing) else 4
        next_steps += f"""{step_num}. ACTION: Automatically add missing skills using add_skills tool.
   DO NOT ask permission. Add them immediately: {', '.join(missing_skills[:5])}
   (Group them by logical categories like Languages, Frameworks, Tools, etc.)
"""
    
    # Check if any major_projects could be portfolio projects
    portfolio_candidates = []
    if work.mcp_details and work.mcp_details.major_projects:
        for project in work.mcp_details.major_projects:
            # Look for indicators this might be a portfolio project
            summary_lower = (project.summary or '').lower()
            name_lower = (project.name or '').lower()
            
            # Strong indicators for automatic addition
            strong_indicators = ['github', 'open source', 'published', 'app store']
            # Weaker indicators - ask first
            weak_indicators = ['side project', 'personal project', 'built', 'created']
            
            if any(keyword in summary_lower or keyword in name_lower for keyword in strong_indicators):
                portfolio_candidates.append((project.name, True))  # True = auto-add
            elif any(keyword in summary_lower for keyword in weak_indicators):
                portfolio_candidates.append((project.name, False))  # False = ask first
    
    current_step = 6 if (has_no_bullets or has_no_projects or missing) else 5
    if missing_skills:
        current_step += 1
    
    if portfolio_candidates:
        auto_add = [name for name, should_auto in portfolio_candidates if should_auto]
        ask_first = [name for name, should_auto in portfolio_candidates if not should_auto]
        
        if auto_add:
            next_steps += f"""{current_step}. ACTION: Automatically add these as top-level portfolio projects using add_project:
   {', '.join(auto_add)}
   These contain GitHub/open source/published indicators.
"""
            current_step += 1
        
        if ask_first:
            next_steps += f"""{current_step}. Ask: "I noticed {', '.join(ask_first[:2])}. 
   {'Is this' if len(ask_first) == 1 else 'Are these'} portfolio project(s) you'd like to showcase on your resume?
   If yes, I'll add {'it' if len(ask_first) == 1 else 'them'} as top-level project(s) using add_project."
"""
            current_step += 1
    
    next_steps += f"""{current_step}. Once position is complete, ask: "Any other work positions to add?"

💡 REMINDER: work[].major_projects provide context for generating resume bullets.
   If the user has portfolio projects (GitHub repos, side projects) to showcase,
   those should be added as top-level projects using add_project."""
    
    return header + basic_info + summary_section + bullets_section + projects_section + tech_section + missing_section + next_steps
