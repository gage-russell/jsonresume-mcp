"""Helper functions for education MCP tools."""

from uuid import uuid4

from resumejson_mcp.lib.experience.models import Education, MCPEducationDetails


def ensure_education_ids(education: Education) -> None:
    """Ensure education has all required IDs set."""
    if not education.mcp_details:
        education.mcp_details = MCPEducationDetails(id=str(uuid4()))
    elif not education.mcp_details.id:
        education.mcp_details.id = str(uuid4())


def detect_missing_info(education: Education) -> list[str]:
    """Identify missing or incomplete information in an education entry."""
    missing = []
    
    if not education.institution:
        missing.append("No institution - specify the school/university name")
    
    if not education.study_type:
        missing.append("No study type - add degree type (e.g., Bachelor's, Master's)")
    
    if not education.area:
        missing.append("No area - specify field of study/major")
    
    if not education.start_date:
        missing.append("No start date - add when you began this program")
    
    if not education.end_date:
        missing.append("No end date - add graduation date or 'Expected YYYY'")
    
    return missing


def format_education_result(education: Education, action: str) -> str:
    """Format an education result for display to the agent."""
    # Header
    header = f"✓ EDUCATION {action.upper()}\n" + "=" * 60 + "\n"
    
    # Basic info
    degree_str = f"{education.study_type}" if education.study_type else "Degree"
    area_str = f" in {education.area}" if education.area else ""
    
    date_range = ""
    if education.start_date or education.end_date:
        start = education.start_date or "?"
        end = education.end_date or "Present"
        date_range = f" ({start} - {end})"
    
    basic_info = f"""\n{degree_str}{area_str}
{education.institution or '(No institution specified)'}{date_range}
ID: {education.mcp_details.id if education.mcp_details else 'N/A'}
"""
    
    if education.score:
        basic_info += f"GPA/Score: {education.score}\n"
    if education.url:
        basic_info += f"URL: {education.url}\n"
    
    # Courses section
    courses_section = ""
    if education.courses:
        courses_section = f"""\n📚 RELEVANT COURSES ({len(education.courses)}):
{', '.join(education.courses)}
"""
    
    # Tags section
    tags_section = ""
    if education.mcp_details and education.mcp_details.tags:
        tags_section = f"""\n🏷️  TAGS:
{', '.join(education.mcp_details.tags)}
"""
    
    # Missing information
    missing = detect_missing_info(education)
    missing_section = ""
    if missing:
        missing_section = f"""\n⚠️  MISSING/INCOMPLETE INFORMATION:
{chr(10).join(f'  • {m}' for m in missing)}

⚠️  IMPORTANT: Ask targeted follow-up questions to complete this information.
"""
    
    # Next steps guidance
    has_missing = len(missing) > 0
    
    next_steps = f"""\n🎯 NEXT STEPS (REQUIRED):
1. Show user the captured information above
2. Ask: "Does this look correct for your education at {education.institution}?"
"""
    
    if has_missing:
        next_steps += f"""3. ⚠️  CRITICAL: This education entry is missing important information.
   Ask specific follow-up questions to complete it.
4. Update the education once you have more information
"""
    else:
        next_steps += f"""3. ✓ This education entry looks complete!
"""
    
    final_step = 5 if has_missing else 4
    next_steps += f"""{final_step}. Ask: "Would you like to add another degree or certification, or move on to work experience or skills?"
"""
    
    return header + basic_info + courses_section + tags_section + missing_section + next_steps
