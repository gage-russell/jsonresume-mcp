"""MCP tools for managing skills."""

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Skill
from resumejson_mcp.lib.pending_actions import get_tracker, ActionType
from resumejson_mcp.mcp.tags import SKILLS_TAGS, CREATE, READ, UPDATE, DELETE, BULK
from resumejson_mcp.mcp.experience.shared_helpers import handle_id_collision
from .helpers import ensure_skill_ids, format_skill_result, format_bulk_skills_result


@tool(
    name="get_all_skills",
    tags=SKILLS_TAGS | {"read"},
    description="""Get all skills from the experience store.

Returns a formatted list of all skill categories with their associated skills.
Use this to see what skills are already captured.

When reviewing skills, check if the categories are well-organized and comprehensive.
If you notice gaps or need clarification, ask the user about missing skills."""
)
def get_all_skills() -> str:
    """Get all skills."""
    store = ExperienceStore()
    skills = store.get_all_skills()
    
    if not skills:
        return """No skills found in experience store.

🎯 NEXT STEPS:
1. Ask user: "What are your main technical skills?"
2. Group skills by category (Languages, Frameworks, Tools, etc.)
3. Use add_skills tool to add multiple categories at once
"""
    
    header = f"📚 ALL SKILL CATEGORIES ({len(skills)})\n" + "=" * 60 + "\n"
    
    result = header
    for skill in skills:
        category_name = skill.name or "(No category)"
        keywords = skill.keywords or []
        level = f" [{skill.level}]" if skill.level else ""
        mcp_id = skill.mcp_details.id if skill.mcp_details else "N/A"
        
        result += f"\n{category_name}{level} (ID: {mcp_id}):\n"
        result += f"  {', '.join(keywords) if keywords else '(No skills listed)'}\n"
    
    return result


@tool(
    name="get_skill_by_id",
    tags=SKILLS_TAGS | {"read"},
    description="""Get a specific skill category by its mcp-details.id.

Use this to view full details of a skill category including:
- Category name and level
- All skills in the category
- Tags for job matching

Args:
    mcp_id: The mcp-details.id of the skill category"""
)
def get_skill_by_id(mcp_id: str) -> str:
    """Get skill by ID."""
    store = ExperienceStore()
    
    try:
        skill = store.get_skill_by_id(mcp_id)
    except ValueError:
        return f"""❌ No skill category found with ID: {mcp_id}

Use get_all_skills to see available skill categories and their IDs."""
    
    return format_skill_result(skill, "retrieved")


@tool(
    name="add_skill",
    tags=SKILLS_TAGS | {"create"},
    description="""Add a single skill category to the experience store.

Use this when adding one skill category at a time, or when you need to capture
detailed information about a specific category.

Args:
    skill: Complete Skill object with name, keywords, and optional level/tags

CRITICAL: A "skill" in this context is a CATEGORY (e.g., "Languages", "Frameworks").
The actual skills go in the keywords array (e.g., ["Python", "JavaScript"]).

Example structure:
{
    "name": "Programming Languages",
    "keywords": ["Python", "JavaScript", "TypeScript", "Go"],
    "level": "Expert",
    "mcp_details": {
        "tags": ["backend", "frontend", "systems"]
    }
}"""
)
def add_skill(skill: Skill) -> str:
    """Add a skill category."""
    ensure_skill_ids(skill)
    
    store = ExperienceStore()
    
    # Check for ID collision
    handle_id_collision(skill, store.get_skill_by_id, ensure_skill_ids)
    
    store.add_skill(skill)
    
    return format_skill_result(skill, "added")


@tool(
    name="add_skills",
    tags=SKILLS_TAGS | {"create", "bulk"},
    description="""Add multiple skill categories at once (bulk operation).

This is the PREFERRED tool when initially capturing skills, as users typically
have multiple categories to add (Languages, Frameworks, Tools, etc.).

Use this to efficiently add several skill categories in one operation.

Args:
    skills: List of Skill objects to add

CRITICAL: A "skill" in this context is a CATEGORY (e.g., "Languages", "Databases").
The actual skills go in each category's keywords array.

Example structure:
[
    {
        "name": "Programming Languages",
        "keywords": ["Python", "JavaScript", "TypeScript"],
        "level": "Expert"
    },
    {
        "name": "Web Frameworks",
        "keywords": ["React", "Django", "FastAPI"],
        "level": "Advanced"
    },
    {
        "name": "Databases",
        "keywords": ["PostgreSQL", "MongoDB", "Redis"]
    }
]

WORKFLOW:
1. Ask user about their main skill areas
2. Group skills by logical categories
3. Use this tool to add all categories at once
4. Follow up for any missing categories"""
)
def add_skills(skills: list[Skill]) -> str:
    """Add multiple skill categories."""
    if not skills:
        return "❌ No skills provided to add"
    
    # Ensure all have IDs
    for skill in skills:
        ensure_skill_ids(skill)
    
    store = ExperienceStore()
    tracker = get_tracker()
    
    # Handle ID collisions
    for skill in skills:
        handle_id_collision(skill, store.get_skill_by_id, ensure_skill_ids)
    
    store.add_skills(skills)
    
    # Auto-complete any pending add_skills actions
    completed = tracker.complete_actions_of_type(ActionType.ADD_SKILLS)
    
    result = format_bulk_skills_result(skills)
    
    if completed > 0:
        result += f"\n\n✓ Auto-completed {completed} pending skill action(s)"
        result += f"\n{tracker.format_compact()}"
    
    return result


@tool(
    name="update_skill",
    tags=SKILLS_TAGS | {"update"},
    description="""Update an existing skill category.

Pass the complete Skill object with mcp_details.id matching the existing category.
This replaces the entire category - any omitted data will be lost.

Use this to:
- Add more skills to a category's keywords
- Update skill level
- Reorganize skills into different categories
- Update tags for better job matching

Args:
    skill: Complete Skill object with mcp_details.id matching existing category"""
)
def update_skill(skill: Skill) -> str:
    """Update a skill category."""
    if not skill.mcp_details or not skill.mcp_details.id:
        return """❌ Cannot update skill: missing mcp_details.id

Use get_all_skills to find the ID of the category you want to update."""
    
    store = ExperienceStore()
    
    try:
        store.get_skill_by_id(skill.mcp_details.id)
    except ValueError:
        return f"""❌ No skill category found with ID: {skill.mcp_details.id}

Use get_all_skills to see available categories and their IDs."""
    
    store.update_skill(skill)
    
    return format_skill_result(skill, "updated")


@tool(
    name="delete_skill",
    tags=SKILLS_TAGS | {"delete"},
    description="""Delete a skill category by its mcp-details.id.

This permanently removes the category and all its associated skills.

CAUTION: This action cannot be undone. Consider updating instead if you just
want to modify the category or reorganize skills.

Args:
    mcp_id: The mcp-details.id of the skill category to delete"""
)
def delete_skill(mcp_id: str) -> str:
    """Delete a skill category."""
    store = ExperienceStore()
    
    try:
        skill = store.get_skill_by_id(mcp_id)
    except ValueError:
        return f"""❌ No skill category found with ID: {mcp_id}

Use get_all_skills to see available categories and their IDs."""
    
    category_name = skill.name or "(No category)"
    skill_count = len(skill.keywords) if skill.keywords else 0
    
    store.delete_skill(mcp_id)
    
    return f"""✓ SKILL CATEGORY DELETED

Category: {category_name}
Skills removed: {skill_count}
ID: {mcp_id}

This category has been permanently removed from the experience store.
"""
