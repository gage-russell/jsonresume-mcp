"""MCP tools for managing job applications."""

from fastmcp.tools import tool

from resumejson_mcp.lib.applications.application_store import ApplicationStore
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Resume


def _validate_resume_content(resume_data: dict, experience_store: ExperienceStore) -> tuple[bool, str, dict]:
    """Validate tailored resume has sufficient content.
    
    Returns:
        (is_valid, error_message, stats_dict)
    """
    errors = []
    warnings = []
    stats = {
        "work_positions_included": 0,
        "work_positions_available": 0,
        "total_highlights": 0,
        "positions_missing_highlights": [],
        "skills_included": 0,
        "skills_available": 0,
        "projects_included": 0,
        "projects_available": 0,
        "bullets_coverage_pct": 0,
        "position_coverage": [],  # Per-position tracking
        "positions_excluded": [],  # Positions not included at all
        "has_key_highlights": False,
        "key_highlights_count": 0,
    }
    
    # Validate keyHighlights - REQUIRED
    key_highlights = resume_data.get("keyHighlights", [])
    stats["key_highlights_count"] = len(key_highlights)
    stats["has_key_highlights"] = len(key_highlights) >= 3
    
    if len(key_highlights) == 0:
        errors.append("❌ keyHighlights is REQUIRED - add 3-5 top achievements that match the job description")
    elif len(key_highlights) < 3:
        warnings.append(f"⚠️  Only {len(key_highlights)} keyHighlights (recommended: 3-5 top achievements)")
    
    # Load full experience for comparison
    try:
        full_experience = experience_store.load_experience()
    except Exception:
        return True, "", stats  # Can't validate without experience data
    
    # Build lookup of experience positions by company+title for matching
    experience_positions = {}
    for work in full_experience.work:
        key = f"{work.position}|{work.name}".lower()
        bullet_count = len(work.mcp_details.bullets) if work.mcp_details and work.mcp_details.bullets else 0
        experience_positions[key] = {
            "position": work.position,
            "company": work.name,
            "available_bullets": bullet_count,
            "included": False,
            "highlights_used": 0,
        }
    
    # Count available content
    stats["work_positions_available"] = len(full_experience.work)
    stats["skills_available"] = len(full_experience.skills)
    stats["projects_available"] = len(full_experience.projects)
    
    total_available_bullets = sum(p["available_bullets"] for p in experience_positions.values())
    
    # Validate work positions and track coverage
    work_entries = resume_data.get("work", [])
    stats["work_positions_included"] = len(work_entries)
    
    if len(work_entries) == 0:
        errors.append("❌ No work positions included - resume must have at least 1 work entry")
    
    # Check minimum positions included (70% of available)
    min_positions_required = max(1, int(len(experience_positions) * 0.7))
    if len(work_entries) < min_positions_required:
        errors.append(f"❌ Only {len(work_entries)} positions included - need at least {min_positions_required} (70% of {len(experience_positions)} available)")
    
    for work in work_entries:
        position = work.get("position", "Unknown")
        company = work.get("name", "Unknown")
        highlights = work.get("highlights", [])
        
        stats["total_highlights"] += len(highlights)
        
        # Try to match to experience position
        key = f"{position}|{company}".lower()
        if key in experience_positions:
            experience_positions[key]["included"] = True
            experience_positions[key]["highlights_used"] = len(highlights)
        
        if len(highlights) == 0:
            errors.append(f"❌ {position} at {company}: No highlights (required: 4-5)")
            stats["positions_missing_highlights"].append(f"{position} at {company}")
        elif len(highlights) < 3:
            errors.append(f"❌ {position} at {company}: Only {len(highlights)} highlights (minimum: 3)")
        elif len(highlights) < 4:
            warnings.append(f"⚠️  {position} at {company}: Only {len(highlights)} highlights (recommended: 4-5)")
    
    # Build per-position coverage stats
    for key, pos_data in experience_positions.items():
        if pos_data["included"]:
            coverage_pct = 0
            if pos_data["available_bullets"] > 0:
                coverage_pct = round((pos_data["highlights_used"] / pos_data["available_bullets"]) * 100)
            stats["position_coverage"].append({
                "position": pos_data["position"],
                "company": pos_data["company"],
                "available": pos_data["available_bullets"],
                "used": pos_data["highlights_used"],
                "coverage_pct": coverage_pct,
            })
        else:
            stats["positions_excluded"].append({
                "position": pos_data["position"],
                "company": pos_data["company"],
                "available": pos_data["available_bullets"],
            })
    
    # Calculate overall bullets coverage
    if total_available_bullets > 0:
        stats["bullets_coverage_pct"] = round((stats["total_highlights"] / total_available_bullets) * 100, 1)
    
    # Validate minimum coverage (60%)
    if stats["bullets_coverage_pct"] < 60 and total_available_bullets > 0:
        errors.append(f"❌ Only {stats['bullets_coverage_pct']}% bullet coverage - need at least 60%")
    
    # Validate skills
    skills = resume_data.get("skills", [])
    stats["skills_included"] = len(skills)
    if len(skills) == 0:
        warnings.append("⚠️  No skills section included")
    
    # Validate projects
    projects = resume_data.get("projects", [])
    stats["projects_included"] = len(projects)
    
    # Build message
    message = ""
    if errors:
        message = "VALIDATION FAILED:\n" + "\n".join(errors)
        if warnings:
            message += "\n\nWARNINGS:\n" + "\n".join(warnings)
        return False, message, stats
    
    if warnings:
        message = "WARNINGS:\n" + "\n".join(warnings)
    
    return True, message, stats


def _format_coverage_report(stats: dict) -> str:
    """Format a coverage report from validation stats."""
    report = "\n📊 CONTENT COVERAGE REPORT\n" + "-" * 50 + "\n"
    
    # Per-position coverage table
    report += "\n📋 POSITION-LEVEL COVERAGE:\n"
    if stats.get("position_coverage"):
        for pos in stats["position_coverage"]:
            status = "✓" if pos["coverage_pct"] >= 50 else "⚠️" if pos["coverage_pct"] > 0 else "❌"
            report += f"  {status} {pos['position']} at {pos['company']}\n"
            report += f"      {pos['used']}/{pos['available']} bullets ({pos['coverage_pct']}%)\n"
    
    # Excluded positions
    if stats.get("positions_excluded"):
        report += "\n❌ POSITIONS NOT INCLUDED:\n"
        for pos in stats["positions_excluded"]:
            report += f"  • {pos['position']} at {pos['company']} ({pos['available']} bullets available)\n"
    
    # Summary stats
    report += "\n" + "-" * 50 + "\n"
    report += f"Work Positions: {stats['work_positions_included']} of {stats['work_positions_available']} included\n"
    report += f"Total Highlights: {stats['total_highlights']} bullets used\n"
    report += f"Overall Coverage: {stats['bullets_coverage_pct']}% of available experience\n"
    report += f"Skills: {stats['skills_included']} of {stats['skills_available']} categories\n"
    report += f"Projects: {stats['projects_included']} of {stats['projects_available']} included\n"
    
    # Key Highlights status
    if stats.get("has_key_highlights"):
        report += f"Key Highlights: ✓ {stats['key_highlights_count']} included\n"
    else:
        report += f"Key Highlights: ❌ {stats['key_highlights_count']} (REQUIRED: 3-5)\n"
    
    if stats.get("positions_missing_highlights"):
        report += f"\n⚠️  Positions with 0 highlights (INVALID):\n"
        for pos in stats["positions_missing_highlights"]:
            report += f"   • {pos}\n"
    
    return report


@tool(
    name="create_job_application",
    description="""Create a new job application folder with job description.
    
    This is the first step in the resume generation workflow:
    1. Create application folder with job description ← YOU ARE HERE
    2. AI generates tailored resume from experience data
    3. Save tailored resume to application
    4. Render to LaTeX and compile to PDF
    
    Args:
        company: Company name
        position: Job position/title
        job_description: The full job description text
        
    Returns:
        Success message with application ID and next steps"""
)
def create_job_application(company: str, position: str, job_description: str) -> str:
    app_store = ApplicationStore()
    
    try:
        app = app_store.create_application(company, position, job_description)
        
        result = "✓ JOB APPLICATION CREATED\n" + "=" * 60 + "\n\n"
        result += f"Application ID: {app.id}\n"
        result += f"Company: {company}\n"
        result += f"Position: {position}\n"
        result += f"Folder: {app.folder_path}\n"
        result += "\n📄 Files created:\n"
        result += f"  • job_description.txt\n"
        result += "\n" + "=" * 60 + "\n"
        result += "🎯 NEXT STEPS - GENERATE TAILORED RESUME:\n"
        result += "=" * 60 + "\n\n"
        result += "1. Use get_experience_for_tailoring() to retrieve the user's full experience\n"
        result += "2. Analyze the job description and select relevant:\n"
        result += "   - Work positions and accomplishments (bullets)\n"
        result += "   - Skills that match the requirements\n"
        result += "   - Projects that demonstrate relevant experience\n"
        result += "3. Craft tailored content:\n"
        result += "   - Select 3-5 best bullets per position\n"
        result += "   - Rewrite bullets to emphasize relevant skills\n"
        result += "   - Prioritize matching keywords from the JD\n"
        result += f"4. Call save_tailored_resume(application_id='{app.id}', resume_data=...)\n"
        result += f"5. Call render_and_compile(application_id='{app.id}')\n"
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="get_experience_for_tailoring",
    description="""Get the user's full experience data for tailoring a resume.
    
    Returns the complete experience.json content which includes:
    - All work positions with mcp-details (bullets, major_projects, tags)
    - All skills with categories
    - All projects
    - Education and basics
    
    CRITICAL - HOW TO USE THIS DATA:
    
    1. PREFER EXISTING BULLETS - Use mcp-details.bullets VERBATIM
       The user has carefully crafted these accomplishments.
       Only modify if you are CERTAIN you can improve them.
    
    2. SELECT, DON'T REWRITE - Pick the most relevant bullets for each position.
       The work[].highlights should mostly be existing bullets selected for relevance.
    
    3. COVERAGE MATTERS - Include 70%+ of positions with 4-5 highlights each.
       Aim for 60%+ overall bullet coverage. More is better.
    
    4. USE MAJOR_PROJECTS FOR CONTEXT - Read them to understand the work,
       but prefer the existing bullet text over creating new content.
    
    5. WHEN TO MODIFY (rare):
       - Adding a specific JD keyword that's genuinely missing
       - Combining two related bullets into one stronger statement
       - Adding quantification when you know the specific metric
    
    Returns:
        JSON string of complete experience data"""
)
def get_experience_for_tailoring() -> str:
    import json
    
    experience_store = ExperienceStore()
    
    try:
        resume = experience_store.load_experience()
        data = resume.model_dump(mode="json", exclude_none=True, by_alias=True)
        
        result = "📋 EXPERIENCE DATA FOR TAILORING\n" + "=" * 60 + "\n\n"
        result += "Use the mcp-details.bullets and mcp-details.major_projects fields\n"
        result += "to select and craft tailored content for the target job.\n\n"
        result += "=" * 60 + "\n\n"
        result += json.dumps(data, indent=2)
        
        return result
    except FileNotFoundError:
        return "❌ ERROR: No experience data found. Add work experience first using add_work()."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="preview_tailored_resume",
    description="""Preview and validate a tailored resume BEFORE saving.
    
    CRITICAL: Always call this tool before save_tailored_resume to verify:
    - All work positions have 3-5 highlights
    - Content coverage is sufficient
    - No positions are missing highlights
    
    This tool validates the resume and shows coverage statistics without saving.
    If validation fails, fix the issues before calling save_tailored_resume.
    
    Args:
        resume_data: The tailored resume as a dict (JSON Resume format)
        
    Returns:
        Validation results with coverage statistics"""
)
def preview_tailored_resume(resume_data: dict) -> str:
    experience_store = ExperienceStore()
    
    is_valid, message, stats = _validate_resume_content(resume_data, experience_store)
    
    result = "📋 RESUME PREVIEW & VALIDATION\n" + "=" * 60 + "\n\n"
    
    # Show keyHighlights first
    key_highlights = resume_data.get("keyHighlights", [])
    if key_highlights:
        result += "⭐ KEY HIGHLIGHTS:\n"
        for i, h in enumerate(key_highlights, 1):
            result += f"  {i}. {h[:80]}{'...' if len(h) > 80 else ''}\n"
        result += "\n"
    else:
        result += "❌ KEY HIGHLIGHTS: MISSING (REQUIRED!)\n\n"
    
    # Show what's included
    result += "📝 WORK POSITIONS INCLUDED:\n"
    work_entries = resume_data.get("work", [])
    for i, work in enumerate(work_entries, 1):
        position = work.get("position", "Unknown")
        company = work.get("name", "Unknown")
        highlights = work.get("highlights", [])
        status = "✓" if len(highlights) >= 3 else "⚠️" if len(highlights) > 0 else "❌"
        result += f"  {status} {i}. {position} at {company} ({len(highlights)} highlights)\n"
    
    result += "\n🎯 SKILLS INCLUDED:\n"
    skills = resume_data.get("skills", [])
    for skill in skills:
        name = skill.get("name", "Unknown")
        keywords = skill.get("keywords", [])
        result += f"  • {name}: {', '.join(keywords[:5])}"
        if len(keywords) > 5:
            result += f" (+{len(keywords)-5} more)"
        result += "\n"
    
    result += "\n🚀 PROJECTS INCLUDED:\n"
    projects = resume_data.get("projects", [])
    for proj in projects:
        name = proj.get("name", "Unknown")
        result += f"  • {name}\n"
    
    # Coverage report
    result += _format_coverage_report(stats)
    
    # Validation result
    result += "\n" + "=" * 60 + "\n"
    if is_valid:
        result += "✅ VALIDATION PASSED\n"
        if message:
            result += f"\n{message}\n"
        result += "\n🎯 NEXT STEP: Call save_tailored_resume() to save this resume.\n"
    else:
        result += "❌ VALIDATION FAILED\n\n"
        result += message + "\n"
        result += "\n⚠️  FIX THE ERRORS ABOVE before calling save_tailored_resume().\n"
        result += "Each work position MUST have at least 3 highlights.\n"
    
    return result


@tool(
    name="save_tailored_resume",
    description="""Save a tailored resume to an application folder.
    
    IMPORTANT: Call preview_tailored_resume() first to validate content!
    
    The resume_data should be a clean JSON Resume object with:
    - basics: Contact information  
    - keyHighlights: 3-5 top achievements matching the job (REQUIRED!)
    - work: Selected positions with tailored highlights (NOT mcp-details)
    - skills: Selected relevant skills
    - projects: Selected relevant projects
    - education: Education entries
    
    REQUIREMENTS:
    - keyHighlights: REQUIRED - 3-5 top achievements tailored to the job description
    - Each work position MUST have at least 3 highlights
    - Highlights should NOT be empty
    - Include relevant skills and projects
    
    DO NOT include mcp-details fields - they will be stripped automatically.
    The work[].highlights should contain the tailored bullet points.
    
    Args:
        application_id: The application ID from create_job_application
        resume_data: The tailored resume as a dict (JSON Resume format)
        
    Returns:
        Success message with file path and coverage stats"""
)
def save_tailored_resume(application_id: str, resume_data: dict) -> str:
    app_store = ApplicationStore()
    experience_store = ExperienceStore()
    
    # Validate content
    is_valid, message, stats = _validate_resume_content(resume_data, experience_store)
    
    if not is_valid:
        result = "❌ RESUME NOT SAVED - VALIDATION FAILED\n" + "=" * 60 + "\n\n"
        result += message + "\n"
        result += _format_coverage_report(stats)
        result += "\n⚠️  FIX THE ERRORS ABOVE and try again.\n"
        result += "TIP: Call preview_tailored_resume() first to check your content.\n"
        return result
    
    try:
        path = app_store.save_resume(application_id, resume_data)
        
        result = "✓ TAILORED RESUME SAVED\n" + "=" * 60 + "\n\n"
        result += f"Application: {application_id}\n"
        result += f"File: {path}\n"
        
        # Show coverage stats
        result += _format_coverage_report(stats)
        
        # Show warnings if any
        if message:
            result += f"\n{message}\n"
        
        result += "\n🎯 NEXT STEP:\n"
        result += f"Call render_and_compile(application_id='{application_id}') to generate the PDF.\n"
        
        return result
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="render_and_compile",
    description="""Render resume to LaTeX and compile to PDF.
    
    This is the final step: takes the resume.json, renders it with the
    Jinja2 template, and compiles to PDF using pdflatex.
    
    Args:
        application_id: The application ID
        template_name: Template to use (default: default.tex.j2)
        
    Returns:
        Success message with PDF path, or error details"""
)
def render_and_compile(application_id: str, template_name: str = "default.tex.j2") -> str:
    app_store = ApplicationStore()
    
    try:
        # First render to LaTeX
        tex_path = app_store.render_to_latex(application_id, template_name)
        
        result = "✓ LATEX RENDERED\n"
        result += f"  File: {tex_path}\n\n"
        
        # Then compile to PDF
        success, message, pdf_path = app_store.compile_to_pdf(application_id)
        
        if success:
            result += "✓ PDF COMPILED\n"
            result += f"  File: {pdf_path}\n\n"
            result += "=" * 60 + "\n"
            result += "🎉 RESUME COMPLETE!\n"
            result += "=" * 60 + "\n\n"
            result += f"Your tailored resume is ready!\n\n"
            # Use markdown links that VS Code can render as clickable
            result += f"📄 **Open PDF:** [resume.pdf](file://{pdf_path})\n\n"
            result += f"📂 **Open Folder:** [View in Finder](file://{pdf_path.parent})\n"
        else:
            result += f"⚠️  PDF COMPILATION FAILED\n"
            result += f"  Error: {message}\n\n"
            result += "The LaTeX file has been generated. You can:\n"
            result += "  1. Fix template issues and try again\n"
            result += "  2. Compile manually with: pdflatex resume.tex\n"
            result += "  3. Upload to Overleaf for online compilation\n"
        
        return result
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="list_applications",
    description="""List all job applications.
    
    Returns:
        Formatted list of all applications with their status"""
)
def list_applications() -> str:
    app_store = ApplicationStore()
    
    try:
        apps = app_store.list_applications()
        
        if not apps:
            return "No applications found. Create one with create_job_application()."
        
        result = "📋 JOB APPLICATIONS\n" + "=" * 60 + "\n\n"
        
        for app in apps:
            status = app_store.get_application_status(app.id)
            
            # Status indicators
            resume_icon = "✓" if status["resume_json"] else "○"
            tex_icon = "✓" if status["resume_tex"] else "○"
            pdf_icon = "✓" if status["resume_pdf"] else "○"
            
            result += f"📁 {app.id}\n"
            result += f"   {app.company} - {app.position}\n"
            result += f"   Created: {app.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            result += f"   Status: [{resume_icon}] resume.json  [{tex_icon}] resume.tex  [{pdf_icon}] resume.pdf\n"
            result += "\n"
        
        result += f"Total: {len(apps)} application(s)\n"
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="get_application",
    description="""Get details of a specific application.
    
    Args:
        application_id: The application ID
        
    Returns:
        Application details including job description and status"""
)
def get_application(application_id: str) -> str:
    app_store = ApplicationStore()
    
    try:
        app = app_store.get_application(application_id)
        
        if app is None:
            return f"❌ Application not found: {application_id}"
        
        status = app_store.get_application_status(application_id)
        
        result = "📋 APPLICATION DETAILS\n" + "=" * 60 + "\n\n"
        result += f"ID: {app.id}\n"
        result += f"Company: {app.company}\n"
        result += f"Position: {app.position}\n"
        result += f"Created: {app.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        result += f"Folder: {app.folder_path}\n\n"
        
        result += "📄 FILES:\n"
        result += f"  {'✓' if status['job_description'] else '○'} job_description.txt\n"
        result += f"  {'✓' if status['resume_json'] else '○'} resume.json\n"
        result += f"  {'✓' if status['resume_tex'] else '○'} resume.tex\n"
        result += f"  {'✓' if status['resume_pdf'] else '○'} resume.pdf\n\n"
        
        result += "📝 JOB DESCRIPTION:\n" + "-" * 40 + "\n"
        result += app.job_description[:1000]
        if len(app.job_description) > 1000:
            result += "\n... (truncated)"
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="delete_application",
    description="""Delete an application and all its files.
    
    Args:
        application_id: The application to delete
        
    Returns:
        Success or error message"""
)
def delete_application(application_id: str) -> str:
    app_store = ApplicationStore()
    
    try:
        deleted = app_store.delete_application(application_id)
        
        if deleted:
            return f"✓ Application deleted: {application_id}"
        else:
            return f"❌ Application not found: {application_id}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="get_application_resume",
    description="""Get the tailored resume.json content from an application.
    
    Args:
        application_id: The application ID
        
    Returns:
        The resume.json content as formatted JSON"""
)
def get_application_resume(application_id: str) -> str:
    import json
    
    app_store = ApplicationStore()
    
    try:
        resume_data = app_store.load_resume(application_id)
        
        if resume_data is None:
            return f"❌ No resume.json found for application: {application_id}\n\nGenerate a tailored resume first using save_tailored_resume()."
        
        result = f"📄 RESUME FOR: {application_id}\n" + "=" * 60 + "\n\n"
        result += json.dumps(resume_data, indent=2)
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"
