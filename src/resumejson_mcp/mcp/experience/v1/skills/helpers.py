"""Helper functions for skills MCP tools."""

from uuid import uuid4

from resumejson_mcp.lib.experience.models import Skill, MCPSkillDetails


def ensure_skill_ids(skill: Skill) -> None:
    """Ensure skill has all required IDs set."""
    if not skill.mcp_details:
        skill.mcp_details = MCPSkillDetails(id=str(uuid4()))
    elif not skill.mcp_details.id:
        skill.mcp_details.id = str(uuid4())


def detect_missing_info(skill: Skill) -> list[str]:
    """Identify missing or incomplete information in a skill entry."""
    missing = []
    
    if not skill.name:
        missing.append("No name - specify the category (e.g., 'Languages', 'Frameworks')")
    
    if not skill.keywords or len(skill.keywords) == 0:
        missing.append("No keywords - list the actual skills in this category")
    
    return missing


def format_skill_result(skill: Skill, action: str) -> str:
    """Format a skill result for display to the agent."""
    # Header
    header = f"✓ SKILL {action.upper()}\n" + "=" * 60 + "\n"
    
    # Basic info
    basic_info = f"""\n{skill.name or '(No category specified)'}
ID: {skill.mcp_details.id if skill.mcp_details else 'N/A'}
"""
    
    if skill.level:
        basic_info += f"Level: {skill.level}\n"
    
    # Keywords section
    keywords_section = ""
    if skill.keywords:
        keywords_section = f"""\n🔧 SKILLS IN THIS CATEGORY ({len(skill.keywords)}):
{', '.join(skill.keywords)}
"""
    
    # Tags section
    tags_section = ""
    if skill.mcp_details and skill.mcp_details.tags:
        tags_section = f"""\n🏷️  TAGS:
{', '.join(skill.mcp_details.tags)}
"""
    
    # Missing information
    missing = detect_missing_info(skill)
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
2. Ask: "Does this look correct for the {skill.name} category?"
"""
    
    if has_missing:
        next_steps += f"""3. ⚠️  CRITICAL: This skill entry is missing important information.
   Ask specific follow-up questions to complete it.
4. Update the skill once you have more information
"""
    else:
        next_steps += f"""3. ✓ This skill category looks complete!
"""
    
    final_step = 5 if has_missing else 4
    next_steps += f"""{final_step}. Ask: "Would you like to add another skill category, or move on to work experience or projects?"

💡 NOTE: Skill.name = category name (e.g., 'Languages', 'Frameworks', 'Tools')
         Skill.keywords = actual skills in that category (e.g., ['Python', 'JavaScript'])
"""
    
    return header + basic_info + keywords_section + tags_section + missing_section + next_steps


def format_bulk_skills_result(skills: list[Skill]) -> str:
    """Format multiple skills result for display."""
    # Group by category
    by_category = {}
    for skill in skills:
        category = skill.name or "(No category)"
        by_category[category] = skill.keywords
    
    header = f"✓ {len(skills)} SKILL CATEGOR{'Y' if len(skills) == 1 else 'IES'} ADDED\n" + "=" * 60 + "\n"
    
    categories_section = "\n"
    for category in sorted(by_category.keys()):
        keywords = by_category[category]
        categories_section += f"\n{category}:\n"
        categories_section += f"  {', '.join(keywords)}\n"
    
    next_steps = f"""\n🎯 NEXT STEPS:
1. Show user the skills added above
2. Ask: "I've added {len(skills)} skill categor{'y' if len(skills) == 1 else 'ies'}. Does everything look correct?"
3. Ask: "Any other skills or categories to add?"
"""
    
    return header + categories_section + next_steps
