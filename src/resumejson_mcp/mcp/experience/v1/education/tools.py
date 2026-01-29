"""MCP tools for managing education entries."""

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Education
from resumejson_mcp.mcp.tags import EDUCATION_TAGS, CREATE, READ, UPDATE, DELETE
from resumejson_mcp.mcp.experience.shared_helpers import handle_id_collision
from resumejson_mcp.mcp.experience.v1.education.helpers import (
    format_education_result,
    ensure_education_ids,
)


@tool(
    name="get_all_education",
    tags=EDUCATION_TAGS | {"read"},
    description="""Get all education entries from experience store.
    
    Returns a formatted list of all education entries with their details.
    Use this to see what education background is already captured."""
)
def get_all_education() -> str:
    store = ExperienceStore()
    education_list = store.get_all_education()
    
    if not education_list:
        return """No education entries found in experience store.

NEXT STEPS:
Ask the user: "Let's add your education background. What's your highest or most recent degree?"
Then use add_education to capture the entry."""
    
    # Format summary
    lines = ["🎓 EDUCATION\n" + "=" * 60]
    for edu in education_list:
        degree = f"{edu.study_type}" if edu.study_type else "Degree"
        area = f" in {edu.area}" if edu.area else ""
        date_range = ""
        if edu.start_date or edu.end_date:
            date_range = f" ({edu.start_date or '?'} - {edu.end_date or 'Present'})"
        
        lines.append(f"\n{degree}{area}")
        lines.append(f"  {edu.institution}{date_range}")
        if edu.score:
            lines.append(f"  • GPA: {edu.score}")
        lines.append(f"  ID: {edu.mcp_details.id if edu.mcp_details else 'N/A'}")
    
    result = "\n".join(lines)
    result += "\n\nNEXT STEPS:\nTo view details of a specific entry, use get_education_by_id."
    result += "\nTo add a new education entry, use add_education."
    
    return result


@tool(
    name="get_education_by_id",
    tags=EDUCATION_TAGS | {"read"},
    description="""Get a specific education entry by its mcp-details.id.
    
    Use this to view full details of an education entry.
    
    Args:
        mcp_id: The mcp-details.id of the education entry"""
)
def get_education_by_id(mcp_id: str) -> str:
    store = ExperienceStore()
    
    try:
        education = store.get_education_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Education entry with ID {mcp_id} not found.

RECOVERY:
Use get_all_education to see existing entries and their IDs."""
    
    return format_education_result(education, action="retrieved")


@tool(
    name="add_education",
    tags=EDUCATION_TAGS | {"create"},
    description="""Add a new education entry.
    
    Capture degree, institution, dates, and other educational background.
    
    Required fields:
    - institution: School/university name
    - study_type: Degree type (e.g., Bachelor's, Master's, Ph.D., Certificate)
    - area: Field of study/major
    - start_date: When you started (ISO 8601 format: YYYY-MM)
    - end_date: Graduation date or expected date (ISO 8601 format: YYYY-MM)
    
    Optional fields:
    - score: GPA or grade (e.g., "3.8/4.0")
    - courses: List of relevant courses
    - url: Link to institution website
    - mcp_details.tags: Keywords for filtering/matching
    
    Args:
        education: Complete Education object"""
)
def add_education(education: Education) -> str:
    store = ExperienceStore()
    
    # Ensure all IDs are set
    ensure_education_ids(education)
    
    # Check for ID collision and regenerate if needed
    handle_id_collision(education, store.get_education_by_id, ensure_education_ids)
    
    store.add_education(education)
    
    return format_education_result(education, action="added")


@tool(
    name="update_education",
    tags=EDUCATION_TAGS | {"update"},
    description="""Update an existing education entry.
    
    Pass the complete Education object with mcp_details.id matching an existing entry.
    
    Args:
        education: Complete Education object with mcp_details.id"""
)
def update_education(education: Education) -> str:
    store = ExperienceStore()
    
    # Verify education exists
    try:
        store.get_education_by_id(education.mcp_details.id)
    except ValueError:
        return f"""✗ ERROR: Education entry with ID {education.mcp_details.id} not found.

RECOVERY:
- Use get_all_education to see existing entries and their IDs
- Or use add_education to create a new entry instead"""
    
    ensure_education_ids(education)
    store.update_education(education.mcp_details.id, education)
    
    return format_education_result(education, action="updated")


@tool(
    name="delete_education",
    tags=EDUCATION_TAGS | {"delete"},
    description="""Delete an education entry by its mcp-details.id.
    
    Args:
        mcp_id: The mcp-details.id of the education entry to delete"""
)
def delete_education(mcp_id: str) -> str:
    store = ExperienceStore()
    
    # Get education first to show what will be deleted
    try:
        education = store.get_education_by_id(mcp_id)
    except ValueError:
        return f"""✗ ERROR: Education entry with ID {mcp_id} not found.

RECOVERY:
Use get_all_education to see existing entries and their IDs."""
    
    store.delete_education(mcp_id)
    
    degree = f"{education.study_type}" if education.study_type else "Degree"
    area = f" in {education.area}" if education.area else ""
    
    return f"""✓ EDUCATION ENTRY DELETED

Removed: {degree}{area}
{education.institution}

NEXT STEPS:
Confirm with user: "I've deleted your {degree}{area} from {education.institution}. Is there anything else you'd like to update?"
"""
