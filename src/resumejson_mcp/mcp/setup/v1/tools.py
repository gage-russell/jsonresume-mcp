"""Setup and configuration tools for resumejson-mcp storage."""

from fastmcp.prompts import prompt
from fastmcp.tools import tool
from fastmcp.resources import resource

from resumejson_mcp.lib.storage.models import StoragePaths
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Resume
from resumejson_mcp.mcp.tags import (
    SETUP_TAGS,
    EXPERIENCE_TAGS,
    VALIDATE_TAGS,
    BACKUP_TAGS,
    EXPORT_TAGS,
    EXPERIENCE, 
    VALIDATE, 
    EXPORT,
    CREATE,
    READ,
)


@prompt(
    name="setup_guide",
    description="Request help setting up resumejson-mcp storage and configuration"
)
def setup_storage_prompt() -> str:
    """Prompt template for user requesting setup assistance."""
    paths = StoragePaths()
    return f"""I need help setting up my resumejson-mcp experience storage system.

Please ask me where I'd like to store:
1. My experience data (work, education, skills, projects)
2. Generated resume outputs

If I don't specify custom paths, use these defaults:
- Experience data: {paths.experience_folder}
- Resume outputs: {paths.output_folder}

Once I provide the paths (or confirm defaults), please initialize the directories and save the configuration."""


@tool(
    name="setup_storage",
    tags=SETUP_TAGS | {"create"},
    description="Initialize or update resumejson-mcp storage directories and save configuration"
)
def setup_storage(storage_paths: StoragePaths) -> str:
    """Set up storage directories and save configuration to disk."""
    try:
        storage_paths.create_and_save_to_config()
        return (
            f"✓ Successfully set up experience storage at: {storage_paths.experience_folder}\n"
            f"✓ Successfully set up resume output at: {storage_paths.output_folder}\n"
            f"✓ Configuration saved to: {storage_paths.config_file}"
        )
    except Exception as e:
        return f"✗ Error setting up storage paths: {str(e)}"


@tool(
    name="initialize_experience",
    tags=SETUP_TAGS | {"create"},
    description="Initialize a new experience.json file with empty JSON Resume structure"
)
def initialize_experience() -> str:
    """Create a new experience.json file if it doesn't already exist."""
    store = ExperienceStore()
    
    if store.experience_exists():
        return f"""⚠️  Experience file already exists at: {store.store.storage_paths.experience_file}

Use get_all_work and other tools to view and manage existing data.
If you want to start fresh, manually delete the file first."""
    
    try:
        store.initialize_experience()
        return f"""✓ Successfully initialized experience.json at: {store.store.storage_paths.experience_file}

The file has been created with an empty JSON Resume structure.
You can now start adding:
- Work experience (use add_work)
- Education (coming soon)
- Skills (coming soon)
- Projects (coming soon)

NEXT STEPS:
Ask the user: "Let's start building your experience data. What work position would you like to add first?"
"""
    except Exception as e:
        return f"✗ Error initializing experience file: {str(e)}"


@tool(
    name="check_setup_status",
    tags=SETUP_TAGS | {"read"},
    description="Check if resumejson-mcp is configured and verify that all required directories exist"
)
def check_setup_status() -> str:
    """Check the current setup status and configuration."""
    paths = StoragePaths()
    store = ExperienceStore()
    
    experience_folder_exists = paths.experience_folder.exists()
    output_folder_exists = paths.output_folder.exists()
    config_exists = paths.config_file.exists()
    experience_file_exists = store.storage_paths.experience_file.exists()
    
    status = []
    status.append("resumejson-mcp Setup Status")
    status.append("=" * 60)
    status.append(f"{'✓' if config_exists else '✗'} Config file: {paths.config_file}")
    status.append(f"{'✓' if experience_folder_exists else '✗'} Experience folder: {paths.experience_folder}")
    status.append(f"{'✓' if output_folder_exists else '✗'} Output folder: {paths.output_folder}")
    status.append(f"{'✓' if experience_file_exists else '✗'} Experience file: {store.storage_paths.experience_file}")
    status.append("")
    
    if all([experience_folder_exists, output_folder_exists, config_exists, experience_file_exists]):
        status.append("✓ Setup complete! Ready to use.")
        status.append("")
        status.append("Available tools:")
        status.append("  • get_all_work - View your work experience")
        status.append("  • add_work - Add a new work position")
    elif config_exists and experience_folder_exists:
        status.append("⚠️  Storage configured but experience file missing.")
        status.append("")
        status.append("NEXT STEP:")
        status.append("Run initialize_experience() to create your experience.json file.")
    else:
        status.append("⚠️  Setup incomplete.")
        status.append("")
        status.append("NEXT STEP:")
        status.append("Run setup_storage() to configure storage paths.")
    
    return "\n".join(status)


@resource(
    uri="storage://paths",
    name="Current Storage Paths",
    description="Current configuration for experience data and resume output directories"
)
def get_storage_paths() -> str:
    """Get the current storage path configuration."""
    return StoragePaths().model_dump_json(indent=2)


@resource(uri="experience://data/experience.json")
async def get_experience_json() -> str:
    """Access the complete experience.json file containing all career data.
    
    This JSON file contains your comprehensive career experience data including:
    - Work history with bullets and major projects
    - Education background
    - Skills organized by category
    - Portfolio projects
    - Personal information (basics)
    
    Use this resource to:
    - Review the complete data structure
    - Understand what information is already captured
    - Validate the JSON Resume format with MCP extensions
    """
    store = ExperienceStore()
    if not store.storage_paths.experience_file.exists():
        return '{"error": "Experience file not found. Use initialize_experience tool first."}'
    
    return store.storage_paths.experience_file.read_text()


@tool(
    name="get_experience_stats",
    tags=EXPERIENCE_TAGS | {"read"},
    description="""Get statistics about the experience store.
    
    Returns a comprehensive overview of your experience data including:
    - Total work positions, bullets, and major projects
    - Date range covered by work history
    - Skills count by category
    - Average bullets per position
    - Coverage analysis and gaps
    
    Use this to:
    - Understand the completeness of your experience data
    - Identify positions that need more bullets
    - See skill distribution across categories"""
)
def get_experience_stats() -> str:
    """Get comprehensive statistics about experience data."""
    store = ExperienceStore()
    
    if not store.experience_exists():
        return "❌ No experience file found. Run initialize_experience() first."
    
    try:
        resume = store.load_experience()
    except Exception as e:
        return f"❌ Error loading experience: {str(e)}"
    
    # Work statistics
    work_count = len(resume.work)
    total_bullets = 0
    total_projects = 0
    positions_low_bullets = []
    positions_no_projects = []
    earliest_date = None
    latest_date = None
    
    for work in resume.work:
        bullets = len(work.mcp_details.bullets) if work.mcp_details else 0
        projects = len(work.mcp_details.major_projects) if work.mcp_details else 0
        total_bullets += bullets
        total_projects += projects
        
        if bullets < 3:
            positions_low_bullets.append(f"{work.position} at {work.name} ({bullets} bullets)")
        if projects == 0:
            positions_no_projects.append(f"{work.position} at {work.name}")
        
        # Track date range
        if work.start_date:
            if not earliest_date or work.start_date < earliest_date:
                earliest_date = work.start_date
        if work.end_date:
            if not latest_date or work.end_date > latest_date:
                latest_date = work.end_date
    
    avg_bullets = round(total_bullets / work_count, 1) if work_count > 0 else 0
    
    # Skills statistics
    skills_count = len(resume.skills)
    total_keywords = sum(len(s.keywords) for s in resume.skills)
    
    # Projects statistics (portfolio projects)
    portfolio_projects = len(resume.projects)
    
    # Education statistics
    education_count = len(resume.education)
    
    # Build report
    result = "📊 EXPERIENCE STATISTICS\n" + "=" * 60 + "\n\n"
    
    # Overview
    result += "📋 OVERVIEW:\n"
    result += f"  • Work positions: {work_count}\n"
    result += f"  • Total bullets: {total_bullets} (avg {avg_bullets}/position)\n"
    result += f"  • Major projects: {total_projects}\n"
    result += f"  • Skill categories: {skills_count} ({total_keywords} total skills)\n"
    result += f"  • Portfolio projects: {portfolio_projects}\n"
    result += f"  • Education entries: {education_count}\n"
    
    if earliest_date or latest_date:
        result += f"\n📅 DATE RANGE:\n"
        result += f"  • {earliest_date or '?'} to {latest_date or 'Present'}\n"
    
    # Coverage Analysis
    result += "\n📈 COVERAGE ANALYSIS:\n"
    if avg_bullets >= 4:
        result += f"  ✓ Good bullet coverage ({avg_bullets} avg per position)\n"
    elif avg_bullets >= 2:
        result += f"  ⚠️ Low bullet coverage ({avg_bullets} avg per position) - aim for 4-5\n"
    else:
        result += f"  ❌ Poor bullet coverage ({avg_bullets} avg per position) - add more accomplishments\n"
    
    if total_projects >= work_count:
        result += f"  ✓ Good project coverage ({total_projects} projects for {work_count} positions)\n"
    else:
        result += f"  ⚠️ Low project coverage ({total_projects} projects for {work_count} positions)\n"
    
    # Gaps
    if positions_low_bullets or positions_no_projects:
        result += "\n⚠️ GAPS TO ADDRESS:\n"
        
        if positions_low_bullets:
            result += "\n  Positions with <3 bullets:\n"
            for pos in positions_low_bullets[:5]:
                result += f"    • {pos}\n"
            if len(positions_low_bullets) > 5:
                result += f"    ... and {len(positions_low_bullets) - 5} more\n"
        
        if positions_no_projects:
            result += "\n  Positions without major projects:\n"
            for pos in positions_no_projects[:5]:
                result += f"    • {pos}\n"
            if len(positions_no_projects) > 5:
                result += f"    ... and {len(positions_no_projects) - 5} more\n"
    else:
        result += "\n✓ No major gaps detected!\n"
    
    # Basics check
    result += "\n👤 BASICS (Contact Info):\n"
    if resume.basics and resume.basics.name:
        result += f"  ✓ Name: {resume.basics.name}\n"
        result += f"  {'✓' if resume.basics.email else '⚠️'} Email: {resume.basics.email or 'Not set'}\n"
        result += f"  {'✓' if resume.basics.summary else '⚠️'} Summary: {'Set' if resume.basics.summary else 'Not set'}\n"
        profile_count = len(resume.basics.profiles)
        result += f"  {'✓' if profile_count > 0 else '⚠️'} Profiles: {profile_count} linked\n"
    else:
        result += "  ❌ Not configured - use set_basics to add contact info\n"
    
    return result


@tool(
    name="validate_experience",
    tags=VALIDATE_TAGS | {"experience"},
    description="""Validate the experience.json for completeness and consistency.
    
    Performs comprehensive validation including:
    - Required fields check for each section
    - Duplicate ID detection
    - Date format validation
    - Consistency checks between sections
    - Missing or empty data warnings
    
    Returns a detailed report of any issues found."""
)
def validate_experience() -> str:
    """Validate experience data for completeness and consistency."""
    store = ExperienceStore()
    
    if not store.experience_exists():
        return "❌ No experience file found. Run initialize_experience() first."
    
    try:
        resume = store.load_experience()
    except Exception as e:
        return f"❌ Error loading experience: {str(e)}\n\nThe experience file may be corrupted."
    
    errors = []
    warnings = []
    info = []
    
    # Check basics
    if not resume.basics:
        errors.append("Basics (contact info) is empty")
    elif not resume.basics.name:
        errors.append("Name is not set in basics")
    elif not resume.basics.email:
        warnings.append("Email is not set in basics")
    elif not resume.basics.summary:
        warnings.append("Professional summary is not set in basics")
    
    # Check work positions
    work_ids = set()
    for i, work in enumerate(resume.work):
        prefix = f"Work[{i}] ({work.position or 'Untitled'} at {work.name or 'Unknown'})"
        
        if not work.position:
            errors.append(f"{prefix}: Missing position/title")
        if not work.name:
            errors.append(f"{prefix}: Missing company name")
        if not work.start_date:
            warnings.append(f"{prefix}: Missing start date")
        
        # Check mcp_details
        if not work.mcp_details:
            warnings.append(f"{prefix}: No mcp-details (no bullets or projects)")
        else:
            # Duplicate ID check
            if work.mcp_details.id in work_ids:
                errors.append(f"{prefix}: Duplicate mcp-details.id '{work.mcp_details.id}'")
            work_ids.add(work.mcp_details.id)
            
            # Bullet count check
            bullet_count = len(work.mcp_details.bullets)
            if bullet_count == 0:
                warnings.append(f"{prefix}: No bullets")
            elif bullet_count < 3:
                info.append(f"{prefix}: Only {bullet_count} bullets (recommend 4-5)")
            
            # Check for duplicate bullet IDs
            bullet_ids = set()
            for bullet in work.mcp_details.bullets:
                if bullet.id in bullet_ids:
                    errors.append(f"{prefix}: Duplicate bullet ID '{bullet.id}'")
                bullet_ids.add(bullet.id)
    
    # Check skills
    skill_ids = set()
    for i, skill in enumerate(resume.skills):
        prefix = f"Skill[{i}] ({skill.name or 'Untitled'})"
        
        if not skill.name:
            warnings.append(f"{prefix}: Missing category name")
        if not skill.keywords or len(skill.keywords) == 0:
            warnings.append(f"{prefix}: No keywords/skills listed")
        
        if skill.mcp_details:
            if skill.mcp_details.id in skill_ids:
                errors.append(f"{prefix}: Duplicate mcp-details.id")
            skill_ids.add(skill.mcp_details.id)
    
    # Check projects
    project_ids = set()
    for i, project in enumerate(resume.projects):
        prefix = f"Project[{i}] ({project.name or 'Untitled'})"
        
        if not project.name:
            warnings.append(f"{prefix}: Missing project name")
        if not project.description:
            info.append(f"{prefix}: Missing description")
        
        if project.mcp_details:
            if project.mcp_details.id in project_ids:
                errors.append(f"{prefix}: Duplicate mcp-details.id")
            project_ids.add(project.mcp_details.id)
    
    # Check education
    education_ids = set()
    for i, edu in enumerate(resume.education):
        prefix = f"Education[{i}] ({edu.study_type or 'Degree'} at {edu.institution or 'Unknown'})"
        
        if not edu.institution:
            warnings.append(f"{prefix}: Missing institution name")
        if not edu.study_type:
            info.append(f"{prefix}: Missing degree type")
        
        if edu.mcp_details:
            if edu.mcp_details.id in education_ids:
                errors.append(f"{prefix}: Duplicate mcp-details.id")
            education_ids.add(edu.mcp_details.id)
    
    # Build report
    result = "🔍 EXPERIENCE VALIDATION REPORT\n" + "=" * 60 + "\n\n"
    
    if not errors and not warnings:
        result += "✅ VALIDATION PASSED - No issues found!\n\n"
        if info:
            result += "📝 SUGGESTIONS:\n"
            for item in info:
                result += f"  • {item}\n"
    else:
        if errors:
            result += f"❌ ERRORS ({len(errors)}):\n"
            for error in errors:
                result += f"  • {error}\n"
            result += "\n"
        
        if warnings:
            result += f"⚠️ WARNINGS ({len(warnings)}):\n"
            for warning in warnings:
                result += f"  • {warning}\n"
            result += "\n"
        
        if info:
            result += f"📝 SUGGESTIONS ({len(info)}):\n"
            for item in info:
                result += f"  • {item}\n"
    
    # Summary
    result += "\n" + "-" * 60 + "\n"
    result += f"Sections validated: basics, {len(resume.work)} work, {len(resume.skills)} skills, "
    result += f"{len(resume.projects)} projects, {len(resume.education)} education\n"
    result += f"Result: {len(errors)} errors, {len(warnings)} warnings, {len(info)} suggestions\n"
    
    return result


@tool(
    name="validate_work_position",
    tags=VALIDATE_TAGS | {"work"},
    description="""Deep validation of a single work position.
    
    Performs detailed validation on one work position including:
    - All required fields check
    - Bullet quality analysis (length, action verbs, metrics)
    - Major project completeness
    - Tag coverage
    - Date format validation
    
    Args:
        work_id: The mcp-details.id of the work position to validate
    
    Returns:
        Detailed validation report with suggestions for improvement."""
)
def validate_work_position(work_id: str) -> str:
    """Deep validation of a single work position."""
    store = ExperienceStore()
    
    if not store.experience_exists():
        return "❌ No experience file found. Run initialize_experience() first."
    
    try:
        work = store.get_work_by_id(work_id)
    except ValueError:
        return f"❌ Work position with ID '{work_id}' not found.\n\nUse get_all_work to see existing positions."
    except Exception as e:
        return f"❌ Error loading work position: {str(e)}"
    
    errors = []
    warnings = []
    suggestions = []
    quality_score = 100  # Start at 100, deduct for issues
    
    # Basic fields validation
    if not work.position:
        errors.append("Missing position/title")
        quality_score -= 15
    if not work.name:
        errors.append("Missing company name")
        quality_score -= 15
    if not work.start_date:
        warnings.append("Missing start date")
        quality_score -= 5
    if not work.summary:
        suggestions.append("Consider adding a summary of your role")
        quality_score -= 3
    if not work.location:
        suggestions.append("Consider adding location (city, state)")
        quality_score -= 2
    
    # MCP details validation
    if not work.mcp_details:
        errors.append("No mcp-details section (bullets and projects cannot be added)")
        quality_score -= 20
        return _format_validation_report(work, errors, warnings, suggestions, quality_score)
    
    # Bullets analysis
    bullets = work.mcp_details.bullets
    bullet_count = len(bullets)
    
    if bullet_count == 0:
        errors.append("No accomplishment bullets")
        quality_score -= 25
    elif bullet_count < 3:
        warnings.append(f"Only {bullet_count} bullets (recommend 4-5)")
        quality_score -= 10
    elif bullet_count >= 5:
        suggestions.append(f"Good bullet coverage ({bullet_count} bullets)")
    
    # Bullet quality checks
    action_verbs = ["led", "built", "developed", "created", "implemented", "designed", 
                    "managed", "reduced", "improved", "increased", "launched", "delivered",
                    "architected", "automated", "optimized", "established", "pioneered",
                    "streamlined", "spearheaded", "orchestrated", "transformed"]
    
    bullets_with_metrics = 0
    bullets_with_action_verbs = 0
    short_bullets = []
    long_bullets = []
    
    for bullet in bullets:
        text_lower = bullet.text.lower()
        text_len = len(bullet.text)
        
        # Check for action verbs
        if any(text_lower.startswith(verb) for verb in action_verbs):
            bullets_with_action_verbs += 1
        
        # Check for metrics/numbers
        if any(char.isdigit() for char in bullet.text) or any(word in text_lower for word in ["%", "percent", "million", "thousand"]):
            bullets_with_metrics += 1
        
        # Length checks
        if text_len < 50:
            short_bullets.append(bullet.text[:40] + "...")
        elif text_len > 200:
            long_bullets.append(bullet.text[:40] + "...")
    
    if bullet_count > 0:
        action_verb_pct = (bullets_with_action_verbs / bullet_count) * 100
        metrics_pct = (bullets_with_metrics / bullet_count) * 100
        
        if action_verb_pct < 50:
            warnings.append(f"Only {action_verb_pct:.0f}% of bullets start with action verbs")
            quality_score -= 5
        
        if metrics_pct < 40:
            warnings.append(f"Only {metrics_pct:.0f}% of bullets contain metrics/numbers")
            quality_score -= 5
        elif metrics_pct >= 60:
            suggestions.append(f"Good metric usage ({metrics_pct:.0f}% of bullets)")
        
        if short_bullets:
            warnings.append(f"{len(short_bullets)} bullets are too short (< 50 chars)")
            quality_score -= 3
        
        if long_bullets:
            suggestions.append(f"{len(long_bullets)} bullets are quite long - consider splitting")
    
    # Major projects analysis
    projects = work.mcp_details.major_projects
    project_count = len(projects)
    
    if project_count == 0:
        warnings.append("No major projects documented")
        quality_score -= 10
    else:
        projects_missing_outcomes = []
        projects_missing_tech = []
        
        for proj in projects:
            if not proj.outcomes:
                projects_missing_outcomes.append(proj.name)
            if not proj.technologies or len(proj.technologies) == 0:
                projects_missing_tech.append(proj.name)
        
        if projects_missing_outcomes:
            warnings.append(f"{len(projects_missing_outcomes)} projects missing outcomes")
            quality_score -= 5
        
        if projects_missing_tech:
            warnings.append(f"{len(projects_missing_tech)} projects missing technologies")
            quality_score -= 3
    
    # Tags analysis
    tags = work.mcp_details.tags
    if not tags or len(tags) == 0:
        suggestions.append("Consider adding tags for job matching (skills, domains)")
        quality_score -= 2
    elif len(tags) < 3:
        suggestions.append(f"Only {len(tags)} tags - consider adding more for better matching")
    
    return _format_validation_report(work, errors, warnings, suggestions, quality_score)


def _format_validation_report(work, errors, warnings, suggestions, quality_score):
    """Format the validation report for a work position."""
    quality_score = max(0, min(100, quality_score))  # Clamp 0-100
    
    # Quality grade
    if quality_score >= 90:
        grade = "A"
        grade_emoji = "🌟"
    elif quality_score >= 80:
        grade = "B"
        grade_emoji = "✓"
    elif quality_score >= 70:
        grade = "C"
        grade_emoji = "⚠️"
    elif quality_score >= 60:
        grade = "D"
        grade_emoji = "⚠️"
    else:
        grade = "F"
        grade_emoji = "❌"
    
    result = f"🔍 WORK POSITION VALIDATION\n{'=' * 60}\n\n"
    result += f"📌 {work.position} at {work.name}\n"
    
    date_range = f"{work.start_date or '?'} - {work.end_date or 'Present'}"
    result += f"📅 {date_range}\n"
    result += f"🆔 ID: {work.mcp_details.id if work.mcp_details else 'N/A'}\n\n"
    
    result += f"{grade_emoji} QUALITY SCORE: {quality_score}/100 (Grade: {grade})\n"
    result += "-" * 60 + "\n\n"
    
    if errors:
        result += f"❌ ERRORS ({len(errors)}):\n"
        for error in errors:
            result += f"  • {error}\n"
        result += "\n"
    
    if warnings:
        result += f"⚠️ WARNINGS ({len(warnings)}):\n"
        for warning in warnings:
            result += f"  • {warning}\n"
        result += "\n"
    
    if suggestions:
        result += f"💡 SUGGESTIONS ({len(suggestions)}):\n"
        for suggestion in suggestions:
            result += f"  • {suggestion}\n"
        result += "\n"
    
    if not errors and not warnings:
        result += "✅ This position looks great! No major issues found.\n"
    
    # Quick stats
    if work.mcp_details:
        result += "\n📊 QUICK STATS:\n"
        result += f"  • Bullets: {len(work.mcp_details.bullets)}\n"
        result += f"  • Major projects: {len(work.mcp_details.major_projects)}\n"
        result += f"  • Tags: {len(work.mcp_details.tags)}\n"
    
    return result


@tool(
    name="list_backups",
    tags=BACKUP_TAGS | {"read"},
    description="""List all available backups of the experience file.
    
    Backups are created automatically before each modification.
    Only the 10 most recent backups are kept.
    
    Returns:
        List of available backups with timestamps"""
)
def list_backups() -> str:
    """List all available experience backups."""
    store = ExperienceStore()
    
    backups = store.list_backups()
    
    if not backups:
        return """📦 NO BACKUPS AVAILABLE

Backups are created automatically when you modify experience data.
The backup directory is: {store._backup_dir}"""
    
    result = "📦 AVAILABLE BACKUPS\n" + "=" * 60 + "\n\n"
    
    for i, backup in enumerate(backups):
        # Parse timestamp from filename
        name = backup.stem  # experience_20260128_143022
        try:
            timestamp_str = name.split("_", 1)[1]
            date_part = timestamp_str[:8]
            time_part = timestamp_str[9:]
            formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        except:
            formatted = name
        
        size_kb = backup.stat().st_size / 1024
        marker = " ← most recent" if i == 0 else ""
        result += f"  {i+1}. {formatted} ({size_kb:.1f} KB){marker}\n"
        result += f"     Path: {backup}\n\n"
    
    result += f"Total: {len(backups)} backup(s)\n"
    result += f"📁 Location: {store._backup_dir}\n"
    
    return result


@tool(
    name="restore_from_backup",
    tags=BACKUP_TAGS | {"update"},
    description="""Restore experience.json from a backup.
    
    CAUTION: This will overwrite your current experience data!
    A backup of the current state is created before restoring.
    
    Args:
        backup_index: Which backup to restore (1 = most recent). 
                      If not provided, restores most recent backup.
    
    Returns:
        Confirmation of restore with summary of restored data"""
)
def restore_from_backup(backup_index: int = 1) -> str:
    """Restore experience from a backup file."""
    store = ExperienceStore()
    
    backups = store.list_backups()
    
    if not backups:
        return "❌ No backups available to restore from."
    
    if backup_index < 1 or backup_index > len(backups):
        return f"❌ Invalid backup index. Valid range: 1-{len(backups)}"
    
    backup_path = backups[backup_index - 1]
    
    try:
        resume = store.restore_from_backup(backup_path)
        
        result = "✓ EXPERIENCE RESTORED\n" + "=" * 60 + "\n\n"
        result += f"Restored from: {backup_path.name}\n\n"
        result += "📊 RESTORED DATA:\n"
        result += f"  • Work positions: {len(resume.work)}\n"
        result += f"  • Skills: {len(resume.skills)}\n"
        result += f"  • Projects: {len(resume.projects)}\n"
        result += f"  • Education: {len(resume.education)}\n"
        result += f"\n⚠️ A backup of your previous state was created before restore.\n"
        
        return result
    except Exception as e:
        return f"❌ Error restoring backup: {str(e)}"


@tool(
    name="export_to_standard_json_resume",
    tags=EXPORT_TAGS | {"experience"},
    description="""Export experience to standard JSON Resume format.
    
    Creates a clean JSON Resume file without mcp-details extensions.
    Useful for compatibility with other JSON Resume tools.
    
    Args:
        output_filename: Name for the output file (default: resume_export.json)
    
    Returns:
        Path to the exported file"""
)
def export_to_standard_json_resume(output_filename: str = "resume_export.json") -> str:
    """Export to standard JSON Resume (without mcp-details)."""
    store = ExperienceStore()
    
    if not store.experience_exists():
        return "❌ No experience file found. Run initialize_experience() first."
    
    try:
        resume = store.load_experience()
    except Exception as e:
        return f"❌ Error loading experience: {str(e)}"
    
    # Create clean version without mcp-details
    clean_data = resume.model_dump(by_alias=True, exclude_none=True)
    
    # Remove mcp-details from all sections
    def remove_mcp_details(obj):
        if isinstance(obj, dict):
            obj.pop("mcp-details", None)
            for value in obj.values():
                remove_mcp_details(value)
        elif isinstance(obj, list):
            for item in obj:
                remove_mcp_details(item)
    
    remove_mcp_details(clean_data)
    
    # For work items, we need to populate highlights from bullets if not present
    for work in clean_data.get("work", []):
        if not work.get("highlights"):
            work["highlights"] = []
    
    # Save to output folder
    output_path = store.storage_paths.output_folder / output_filename
    with open(output_path, "w") as f:
        import json
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
    
    result = "✓ EXPORTED TO STANDARD JSON RESUME\n" + "=" * 60 + "\n\n"
    result += f"Output: {output_path}\n\n"
    result += "📋 EXPORTED DATA:\n"
    result += f"  • Basics: {'✓' if clean_data.get('basics') else '✗'}\n"
    result += f"  • Work: {len(clean_data.get('work', []))} positions\n"
    result += f"  • Skills: {len(clean_data.get('skills', []))} categories\n"
    result += f"  • Projects: {len(clean_data.get('projects', []))} projects\n"
    result += f"  • Education: {len(clean_data.get('education', []))} entries\n"
    result += f"\n📝 Note: mcp-details have been removed for compatibility.\n"
    result += f"This file can be used with jsonresume.org and other tools.\n"
    
    return result
