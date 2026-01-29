"""MCP tools for searching and filtering experience data."""

import re
from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore


def _normalize_text(text: str) -> str:
    """Normalize text for case-insensitive search."""
    return text.lower().strip()


def _text_matches(query: str, text: str | None) -> bool:
    """Check if query matches text (case-insensitive, partial match)."""
    if not text:
        return False
    return query in _normalize_text(text)


def _highlight_match(text: str, query: str) -> str:
    """Highlight matching text with markers."""
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"**{m.group()}**", text)


@tool(
    name="search_experience",
    description="""Full-text search across all experience data.
    
    Searches through:
    - Work: position titles, company names, summaries, bullet text, major project content
    - Skills: category names and keywords
    - Projects: names, descriptions, highlights
    - Education: institution, area of study, degree
    
    Args:
        query: Search term (case-insensitive)
        sections: Optional list to limit search - ["work", "skills", "projects", "education"]
                  If not provided, searches all sections.
    
    Returns:
        Formatted list of matching items with context"""
)
def search_experience(query: str, sections: list[str] | None = None) -> str:
    if not query or len(query.strip()) < 2:
        return "❌ Query must be at least 2 characters."
    
    store = ExperienceStore()
    
    try:
        experience = store.load_experience()
    except FileNotFoundError:
        return "❌ Experience file not found. Run initialize_experience() first."
    
    query_lower = _normalize_text(query)
    valid_sections = {"work", "skills", "projects", "education"}
    
    if sections:
        sections = [s.lower() for s in sections]
        invalid = set(sections) - valid_sections
        if invalid:
            return f"❌ Invalid sections: {invalid}. Valid: {valid_sections}"
    else:
        sections = list(valid_sections)
    
    results = []
    
    # Search Work
    if "work" in sections:
        work_matches = []
        for work in experience.work:
            matches_in_position = []
            
            # Search core fields
            if _text_matches(query_lower, work.position):
                matches_in_position.append(f"Position: {work.position}")
            if _text_matches(query_lower, work.name):
                matches_in_position.append(f"Company: {work.name}")
            if _text_matches(query_lower, work.summary):
                matches_in_position.append(f"Summary matches")
            
            # Search bullets
            if work.mcp_details:
                for bullet in work.mcp_details.bullets:
                    if _text_matches(query_lower, bullet.text):
                        highlighted = _highlight_match(bullet.text, query)
                        matches_in_position.append(f"Bullet: {highlighted[:100]}...")
                
                # Search major projects
                for proj in work.mcp_details.major_projects:
                    if _text_matches(query_lower, proj.name):
                        matches_in_position.append(f"Major Project: {proj.name}")
                    if _text_matches(query_lower, proj.summary):
                        matches_in_position.append(f"Project Summary matches: {proj.name}")
                    if any(_text_matches(query_lower, tech) for tech in proj.technologies):
                        matching_tech = [t for t in proj.technologies if _text_matches(query_lower, t)]
                        matches_in_position.append(f"Technologies in {proj.name}: {', '.join(matching_tech)}")
                
                # Search tags
                matching_tags = [t for t in work.mcp_details.tags if _text_matches(query_lower, t)]
                if matching_tags:
                    matches_in_position.append(f"Tags: {', '.join(matching_tags)}")
            
            if matches_in_position:
                work_id = work.mcp_details.id if work.mcp_details else "N/A"
                date_range = f"{work.start_date or '?'} - {work.end_date or 'Present'}"
                work_matches.append({
                    "header": f"{work.position} at {work.name} ({date_range})",
                    "id": work_id,
                    "matches": matches_in_position,
                })
        
        if work_matches:
            results.append(("WORK EXPERIENCE", work_matches))
    
    # Search Skills
    if "skills" in sections:
        skill_matches = []
        for skill in experience.skills:
            matches_in_skill = []
            
            if _text_matches(query_lower, skill.name):
                matches_in_skill.append(f"Category: {skill.name}")
            
            matching_keywords = [kw for kw in skill.keywords if _text_matches(query_lower, kw)]
            if matching_keywords:
                matches_in_skill.append(f"Keywords: {', '.join(matching_keywords)}")
            
            if matches_in_skill:
                skill_id = skill.mcp_details.id if skill.mcp_details else "N/A"
                skill_matches.append({
                    "header": f"{skill.name}",
                    "id": skill_id,
                    "matches": matches_in_skill,
                })
        
        if skill_matches:
            results.append(("SKILLS", skill_matches))
    
    # Search Projects
    if "projects" in sections:
        project_matches = []
        for proj in experience.projects:
            matches_in_project = []
            
            if _text_matches(query_lower, proj.name):
                matches_in_project.append(f"Name: {proj.name}")
            if _text_matches(query_lower, proj.description):
                matches_in_project.append(f"Description matches")
            
            matching_keywords = [kw for kw in (proj.keywords or []) if _text_matches(query_lower, kw)]
            if matching_keywords:
                matches_in_project.append(f"Keywords: {', '.join(matching_keywords)}")
            
            matching_highlights = [h for h in (proj.highlights or []) if _text_matches(query_lower, h)]
            if matching_highlights:
                matches_in_project.append(f"Highlights: {len(matching_highlights)} match(es)")
            
            if matches_in_project:
                proj_id = proj.mcp_details.id if proj.mcp_details else "N/A"
                project_matches.append({
                    "header": f"{proj.name}",
                    "id": proj_id,
                    "matches": matches_in_project,
                })
        
        if project_matches:
            results.append(("PROJECTS", project_matches))
    
    # Search Education
    if "education" in sections:
        edu_matches = []
        for edu in experience.education:
            matches_in_edu = []
            
            if _text_matches(query_lower, edu.institution):
                matches_in_edu.append(f"Institution: {edu.institution}")
            if _text_matches(query_lower, edu.area):
                matches_in_edu.append(f"Area: {edu.area}")
            if _text_matches(query_lower, edu.study_type):
                matches_in_edu.append(f"Degree: {edu.study_type}")
            
            matching_courses = [c for c in (edu.courses or []) if _text_matches(query_lower, c)]
            if matching_courses:
                matches_in_edu.append(f"Courses: {', '.join(matching_courses[:3])}")
            
            if matches_in_edu:
                edu_id = edu.mcp_details.id if edu.mcp_details else "N/A"
                edu_matches.append({
                    "header": f"{edu.study_type or 'Degree'} at {edu.institution}",
                    "id": edu_id,
                    "matches": matches_in_edu,
                })
        
        if edu_matches:
            results.append(("EDUCATION", edu_matches))
    
    # Format output
    if not results:
        return f"""🔍 No results found for "{query}" in sections: {', '.join(sections)}

Try:
- Using different keywords
- Searching across all sections (omit sections parameter)
- Using partial words (e.g., "python" instead of "Python 3.10")"""
    
    lines = [f'🔍 SEARCH RESULTS for "{query}"', "=" * 60]
    total_matches = 0
    
    for section_name, matches in results:
        lines.append(f"\n📂 {section_name} ({len(matches)} match(es))")
        lines.append("-" * 40)
        for match in matches:
            total_matches += 1
            lines.append(f"\n  {match['header']}")
            lines.append(f"  ID: {match['id']}")
            for m in match["matches"][:5]:  # Limit to 5 matches per item
                lines.append(f"    • {m}")
            if len(match["matches"]) > 5:
                lines.append(f"    ... +{len(match['matches']) - 5} more matches")
    
    lines.append(f"\n{'=' * 60}")
    lines.append(f"Total: {total_matches} item(s) matched across {len(results)} section(s)")
    
    return "\n".join(lines)


@tool(
    name="filter_work_by_tags",
    description="""Filter work positions by tags.
    
    Tags can be skills, technologies, domains, or any labels added to work positions.
    Searches both position-level tags and project-level tags.
    
    Args:
        tags: List of tags to filter by
        match_all: If True, position must have ALL tags. If False (default), position must have ANY tag.
    
    Returns:
        Filtered list of work positions with matching tags highlighted"""
)
def filter_work_by_tags(tags: list[str], match_all: bool = False) -> str:
    if not tags:
        return "❌ At least one tag is required."
    
    store = ExperienceStore()
    
    try:
        work_list = store.get_all_work()
    except FileNotFoundError:
        return "❌ Experience file not found. Run initialize_experience() first."
    
    if not work_list:
        return "No work positions in experience store."
    
    # Normalize tags for comparison
    search_tags = {_normalize_text(t) for t in tags}
    
    matches = []
    
    for work in work_list:
        if not work.mcp_details:
            continue
        
        # Collect all tags from position and projects
        position_tags = {_normalize_text(t) for t in work.mcp_details.tags}
        project_tags = set()
        project_techs = set()
        
        for proj in work.mcp_details.major_projects:
            project_tags.update(_normalize_text(t) for t in proj.tags)
            project_techs.update(_normalize_text(t) for t in proj.technologies)
        
        all_position_tags = position_tags | project_tags | project_techs
        
        # Check for match
        matched_tags = search_tags & all_position_tags
        
        if match_all:
            if matched_tags == search_tags:  # All tags present
                matches.append((work, matched_tags))
        else:
            if matched_tags:  # Any tag present
                matches.append((work, matched_tags))
    
    if not matches:
        mode = "all of" if match_all else "any of"
        return f"""🔍 No work positions found with {mode} tags: {', '.join(tags)}

Available tags in your experience:
{_get_all_tags_summary(work_list)}

Try using different or fewer tags."""
    
    # Format results
    mode_desc = "ALL" if match_all else "ANY"
    lines = [
        f"🔍 WORK FILTERED BY TAGS ({mode_desc} of: {', '.join(tags)})",
        "=" * 60,
        f"Found {len(matches)} position(s):\n"
    ]
    
    for work, matched_tags in matches:
        date_range = f"{work.start_date or '?'} - {work.end_date or 'Present'}"
        bullet_count = len(work.mcp_details.bullets)
        project_count = len(work.mcp_details.major_projects)
        
        lines.append(f"📌 {work.position} at {work.name}")
        lines.append(f"   {date_range}")
        lines.append(f"   ID: {work.mcp_details.id}")
        lines.append(f"   Matched tags: {', '.join(sorted(matched_tags))}")
        lines.append(f"   Content: {bullet_count} bullets, {project_count} major projects")
        lines.append("")
    
    return "\n".join(lines)


def _get_all_tags_summary(work_list) -> str:
    """Get a summary of all unique tags across work positions."""
    all_tags = set()
    all_techs = set()
    
    for work in work_list:
        if work.mcp_details:
            all_tags.update(work.mcp_details.tags)
            for proj in work.mcp_details.major_projects:
                all_tags.update(proj.tags)
                all_techs.update(proj.technologies)
    
    lines = []
    if all_tags:
        tag_preview = ', '.join(sorted(all_tags)[:15])
        lines.append(f"  Tags: {tag_preview}" + (f"\n        (+{len(all_tags) - 15} more)" if len(all_tags) > 15 else ""))
    if all_techs:
        tech_preview = ', '.join(sorted(all_techs)[:15])
        lines.append(f"  Tech: {tech_preview}" + (f"\n        (+{len(all_techs) - 15} more)" if len(all_techs) > 15 else ""))
    
    return "\n".join(lines) if lines else "  (no tags found)"
