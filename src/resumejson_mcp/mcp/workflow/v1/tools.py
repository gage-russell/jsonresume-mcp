"""MCP tools for workflow and pending actions management."""

from fastmcp.tools import tool

from resumejson_mcp.lib.pending_actions import get_tracker, ActionType, ActionPriority
from resumejson_mcp.mcp.tags import WORKFLOW_TAGS, TODO_TAGS, ANALYZE_TAGS, READ, CREATE, DELETE


@tool(
    name="get_pending_todos",
    tags=TODO_TAGS | {"read"},
    description="""Get all pending actions that need to be completed.
    
    IMPORTANT: Call this tool frequently to check if you have pending work to complete.
    Pending actions are created automatically when you:
    - Add work positions (missing skills, projects, bullets are tracked)
    - Perform operations that require follow-up
    
    Priority levels:
    - CRITICAL: Must complete before moving on (e.g., missing bullets/projects)
    - HIGH: Should complete soon (e.g., adding extracted skills)
    - MEDIUM: Can defer but shouldn't forget (e.g., portfolio projects)
    - LOW: Nice to have
    
    Returns:
        Summary of all pending actions grouped by priority"""
)
def get_pending_todos() -> str:
    tracker = get_tracker()
    
    incomplete = tracker.get_incomplete_actions()
    
    if not incomplete:
        return """✅ NO PENDING ACTIONS

All tasks are complete! You can:
- Add more work experience with add_work
- Generate a tailored resume for a job
- Ask the user what they'd like to do next"""
    
    result = tracker.format_summary()
    
    # Add guidance on how to complete each type
    result += """

📖 HOW TO COMPLETE ACTIONS:

🔴 CRITICAL - add_bullets / add_major_project:
   Use add_bullet_to_work(work_id, bullet) or add_major_project_to_work(work_id, project)
   Ask user for accomplishments and project details if needed

🟠 HIGH - add_skills:
   Use add_skills(skills) to add skill categories with keywords
   Group extracted technologies into logical categories (Languages, Frameworks, Tools, etc.)

🟡 MEDIUM - add_project (portfolio):
   Ask user if they want to showcase these as portfolio projects
   If yes, use add_project(project) to create top-level portfolio entry

🟢 LOW - cleanup:
   Can be deferred, complete when convenient

Use complete_todo(action_id) to mark an action as done after completing it."""
    
    return result


@tool(
    name="complete_todo",
    tags=TODO_TAGS | {"update"},
    description="""Mark a pending action as completed.
    
    Call this after you've completed an action to remove it from the pending list.
    
    Args:
        action_id: The ID of the action to mark complete
        
    Returns:
        Confirmation and remaining pending actions count"""
)
def complete_todo(action_id: str) -> str:
    tracker = get_tracker()
    
    action = tracker.get_action(action_id)
    if not action:
        return f"""❌ Action not found: {action_id}

Use get_pending_todos to see current pending actions and their IDs."""
    
    if action.completed:
        return f"""⚠️ Action already completed: {action.description}"""
    
    action.mark_completed()
    
    remaining = tracker.get_incomplete_actions()
    
    return f"""✓ COMPLETED: {action.description}

{tracker.format_compact()}"""


@tool(
    name="complete_todos_of_type",
    tags=TODO_TAGS | {"update", "bulk"},
    description="""Mark all pending actions of a specific type as completed.
    
    Useful when you've completed a batch of related actions (e.g., added all missing skills).
    
    Args:
        action_type: One of: add_skills, add_major_project, add_bullets, add_project, 
                     confirm_with_user, extract_more_info, update_work, delete_duplicate
        target_id: Optional - only complete actions for this specific target (work_id, etc.)
        
    Returns:
        Count of actions completed and remaining pending actions"""
)
def complete_todos_of_type(action_type: str, target_id: str | None = None) -> str:
    tracker = get_tracker()
    
    # Map string to enum
    type_map = {
        "add_skills": ActionType.ADD_SKILLS,
        "add_major_project": ActionType.ADD_MAJOR_PROJECT,
        "add_bullets": ActionType.ADD_BULLETS,
        "add_project": ActionType.ADD_PROJECT,
        "confirm_with_user": ActionType.CONFIRM_WITH_USER,
        "extract_more_info": ActionType.EXTRACT_MORE_INFO,
        "update_work": ActionType.UPDATE_WORK,
        "delete_duplicate": ActionType.DELETE_DUPLICATE,
    }
    
    if action_type not in type_map:
        return f"""❌ Invalid action_type: {action_type}

Valid types: {', '.join(type_map.keys())}"""
    
    completed_count = tracker.complete_actions_of_type(type_map[action_type], target_id)
    
    if completed_count == 0:
        return f"""⚠️ No pending actions of type '{action_type}' found."""
    
    return f"""✓ COMPLETED {completed_count} action(s) of type '{action_type}'

{tracker.format_compact()}"""


@tool(
    name="clear_completed_todos",
    tags=TODO_TAGS | {"delete"},
    description="""Remove all completed actions from the tracker.
    
    Use this to clean up the action list after a batch of work.
    
    Returns:
        Count of actions cleared"""
)
def clear_completed_todos() -> str:
    tracker = get_tracker()
    
    cleared = tracker.clear_completed()
    remaining = len(tracker.get_incomplete_actions())
    
    return f"""✓ Cleared {cleared} completed action(s)
📋 {remaining} action(s) still pending

{tracker.format_compact()}"""


@tool(
    name="add_custom_todo",
    tags=TODO_TAGS | {"create"},
    description="""Add a custom pending action for tracking.
    
    Use this to add your own reminders or tasks that should be tracked
    alongside the automatically generated pending actions.
    
    Args:
        description: What needs to be done
        priority: One of: critical, high, medium, low (default: medium)
        target_id: Optional - ID of related entity (work_id, project_id, etc.)
        
    Returns:
        Confirmation with the new action details"""
)
def add_custom_todo(
    description: str,
    priority: str = "medium",
    target_id: str | None = None,
) -> str:
    tracker = get_tracker()
    
    # Map string to priority enum
    priority_map = {
        "critical": ActionPriority.CRITICAL,
        "high": ActionPriority.HIGH,
        "medium": ActionPriority.MEDIUM,
        "low": ActionPriority.LOW,
    }
    
    if priority.lower() not in priority_map:
        return f"""❌ Invalid priority: {priority}

Valid priorities: critical, high, medium, low"""
    
    action = tracker.add_action(
        action_type=ActionType.CONFIRM_WITH_USER,  # Using this as generic custom type
        priority=priority_map[priority.lower()],
        description=description,
        target_id=target_id,
    )
    
    emoji = {
        ActionPriority.CRITICAL: "🔴",
        ActionPriority.HIGH: "🟠",
        ActionPriority.MEDIUM: "🟡",
        ActionPriority.LOW: "🟢",
    }[action.priority]
    
    return f"""✓ Added custom todo:
{emoji} [{action.priority.value.upper()}] {description}
ID: {action.id}
{f'Target: {target_id}' if target_id else ''}

{tracker.format_compact()}"""


@tool(
    name="get_pending_todos_for_work",
    tags=TODO_TAGS | {"read"},
    description="""Get pending actions specific to a work position.
    
    Filters pending actions to show only those related to a specific work ID.
    Useful for focusing on completing tasks for one position at a time.
    
    Args:
        work_id: The mcp-details.id of the work position
        
    Returns:
        Pending actions for that specific position"""
)
def get_pending_todos_for_work(work_id: str) -> str:
    tracker = get_tracker()
    
    actions = tracker.get_actions_for_target(work_id)
    
    if not actions:
        return f"""✅ No pending actions for work ID: {work_id}

This position is complete! Use get_pending_todos to see all pending actions."""
    
    def format_action(action):
        emoji = {
            ActionPriority.CRITICAL: "🔴",
            ActionPriority.HIGH: "🟠",
            ActionPriority.MEDIUM: "🟡",
            ActionPriority.LOW: "🟢",
        }[action.priority]
        lines = [
            f"\n{emoji} [{action.priority.value.upper()}] {action.description}",
            f"   ID: {action.id}",
            f"   Type: {action.action_type.value}"
        ]
        if action.items:
            items_preview = ", ".join(action.items[:5])
            if len(action.items) > 5:
                items_preview += f" (+{len(action.items) - 5} more)"
            lines.append(f"   Items: {items_preview}")
        return "\n".join(lines)
    
    header = [f"📋 PENDING ACTIONS for work ID: {work_id}", "=" * 60]
    action_details = [format_action(a) for a in actions]
    footer = [f"\nTotal: {len(actions)} pending action(s) for this position"]
    
    return "\n".join(header + action_details + footer)


@tool(
    name="analyze_job_description",
    tags=ANALYZE_TAGS,
    description="""Analyze a job description to extract key requirements and keywords.
    
    This tool parses a job description to identify:
    - Required skills and technologies
    - Preferred/nice-to-have skills
    - Key responsibilities
    - Experience requirements
    - Keywords for ATS optimization
    
    Use this BEFORE tailoring a resume to understand what to emphasize.
    
    Args:
        job_description: The full job description text
        
    Returns:
        Structured analysis of the job requirements"""
)
def analyze_job_description(job_description: str) -> str:
    """Analyze a job description to extract key requirements."""
    import re
    
    lines = job_description.split('\n')
    text_lower = job_description.lower()
    
    result = "📋 JOB DESCRIPTION ANALYSIS\n" + "=" * 70 + "\n\n"
    
    # Common technical skills to look for
    tech_skills = [
        # Languages
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "ruby", "scala", "kotlin", "swift", "php", "perl", "r",
        # Frameworks
        "react", "angular", "vue", "node.js", "nodejs", "django", "flask",
        "fastapi", "spring", "rails", "express", ".net", "nextjs", "next.js",
        # Cloud
        "aws", "azure", "gcp", "google cloud", "cloud", "kubernetes", "k8s",
        "docker", "terraform", "ansible", "cloudformation", "pulumi",
        # Data
        "sql", "postgresql", "postgres", "mysql", "mongodb", "redis",
        "elasticsearch", "kafka", "spark", "hadoop", "snowflake", "databricks",
        "airflow", "dagster", "dbt", "pandas", "numpy", "pytorch", "tensorflow",
        # DevOps
        "ci/cd", "jenkins", "github actions", "gitlab", "circleci",
        "prometheus", "grafana", "datadog", "splunk", "observability",
        # Concepts
        "microservices", "api", "rest", "graphql", "grpc", "distributed systems",
        "machine learning", "ml", "ai", "nlp", "data engineering", "etl",
        "data pipeline", "data warehouse", "agile", "scrum", "devops", "sre",
    ]
    
    found_skills = []
    for skill in tech_skills:
        # Check for word boundaries to avoid false positives
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
    
    # Deduplicate while preserving order
    found_skills = list(dict.fromkeys(found_skills))
    
    result += "🔧 TECHNICAL SKILLS DETECTED\n"
    result += "-" * 40 + "\n"
    if found_skills:
        # Group into rows of 5
        for i in range(0, len(found_skills), 5):
            result += "  " + ", ".join(found_skills[i:i+5]) + "\n"
    else:
        result += "  (No common technical skills detected)\n"
    
    # Look for experience level requirements
    result += "\n📊 EXPERIENCE REQUIREMENTS\n"
    result += "-" * 40 + "\n"
    
    experience_patterns = [
        (r'(\d+)\+?\s*years?\s*(of)?\s*(experience|exp)', "Years of experience"),
        (r'(senior|sr\.?)\s', "Senior level"),
        (r'(junior|jr\.?)\s', "Junior level"),
        (r'(staff|principal|lead)\s', "Staff/Principal level"),
        (r'(entry[- ]level|new grad)', "Entry level"),
    ]
    
    exp_found = []
    for pattern, label in experience_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if "years" in label.lower():
                exp_found.append(f"  • {match.group(1)}+ years required")
            else:
                exp_found.append(f"  • {label} indicated")
    
    if exp_found:
        result += "\n".join(exp_found) + "\n"
    else:
        result += "  (No specific experience requirements detected)\n"
    
    # Look for responsibility keywords
    result += "\n📋 KEY RESPONSIBILITIES (keywords)\n"
    result += "-" * 40 + "\n"
    
    responsibility_keywords = [
        "design", "build", "develop", "implement", "architect", "lead",
        "mentor", "collaborate", "optimize", "scale", "maintain", "deploy",
        "monitor", "debug", "troubleshoot", "automate", "integrate", "migrate",
        "manage", "own", "drive", "deliver", "support", "review", "test",
    ]
    
    found_responsibilities = []
    for kw in responsibility_keywords:
        if re.search(r'\b' + kw + r'\w*\b', text_lower):
            found_responsibilities.append(kw.capitalize())
    
    if found_responsibilities:
        for i in range(0, len(found_responsibilities), 6):
            result += "  " + ", ".join(found_responsibilities[i:i+6]) + "\n"
    else:
        result += "  (No specific responsibilities detected)\n"
    
    # Look for soft skills
    result += "\n🤝 SOFT SKILLS / VALUES\n"
    result += "-" * 40 + "\n"
    
    soft_skills = [
        "communication", "teamwork", "collaboration", "leadership",
        "problem-solving", "analytical", "creative", "innovative",
        "self-motivated", "autonomous", "detail-oriented", "organized",
        "fast-paced", "agile", "flexible", "adaptable", "passionate",
    ]
    
    found_soft = []
    for skill in soft_skills:
        if skill in text_lower:
            found_soft.append(skill.title())
    
    if found_soft:
        result += "  " + ", ".join(found_soft) + "\n"
    else:
        result += "  (No specific soft skills emphasized)\n"
    
    # Extract what looks like required vs preferred
    result += "\n⚡ REQUIRED vs NICE-TO-HAVE\n"
    result += "-" * 40 + "\n"
    
    required_section = False
    preferred_section = False
    required_items = []
    preferred_items = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if any(x in line_lower for x in ["required", "must have", "requirements:", "qualifications:"]):
            required_section = True
            preferred_section = False
        elif any(x in line_lower for x in ["preferred", "nice to have", "bonus", "plus", "ideally"]):
            required_section = False
            preferred_section = True
        elif line.strip() == "" or (line.strip().startswith("#") and len(line.strip()) < 50):
            required_section = False
            preferred_section = False
        elif required_section and line.strip().startswith(("•", "-", "*", "·")):
            required_items.append(line.strip()[1:].strip()[:80])
        elif preferred_section and line.strip().startswith(("•", "-", "*", "·")):
            preferred_items.append(line.strip()[1:].strip()[:80])
    
    if required_items:
        result += "  REQUIRED:\n"
        for item in required_items[:7]:
            result += f"    • {item}\n"
        if len(required_items) > 7:
            result += f"    ... and {len(required_items) - 7} more\n"
    
    if preferred_items:
        result += "\n  PREFERRED:\n"
        for item in preferred_items[:5]:
            result += f"    • {item}\n"
        if len(preferred_items) > 5:
            result += f"    ... and {len(preferred_items) - 5} more\n"
    
    if not required_items and not preferred_items:
        result += "  (Could not parse required/preferred sections - check formatting)\n"
    
    # Summary recommendations
    result += "\n" + "=" * 70 + "\n"
    result += "💡 TAILORING RECOMMENDATIONS\n"
    result += "=" * 70 + "\n\n"
    
    result += "1. PRIORITIZE these skills in your highlights:\n"
    if found_skills:
        priority_skills = found_skills[:10]
        result += f"   {', '.join(priority_skills)}\n"
    
    result += "\n2. EMPHASIZE these action themes:\n"
    if found_responsibilities:
        result += f"   {', '.join(found_responsibilities[:8])}\n"
    
    result += "\n3. CONSIDER adding these if you have them:\n"
    if found_soft:
        result += f"   {', '.join(found_soft[:5])}\n"
    
    result += "\n4. ATS KEYWORD DENSITY: Include exact phrases from the JD\n"
    result += "   Copy key phrases verbatim where truthful\n"
    
    return result
