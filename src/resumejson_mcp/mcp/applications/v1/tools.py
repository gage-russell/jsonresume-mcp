"""MCP tools for managing job applications."""

from fastmcp.tools import tool

from resumejson_mcp.lib.applications.application_store import ApplicationStore
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.mcp.tags import (
    APP_TAGS, 
    COVER_LETTER_TAGS, 
    RESUME_WORKFLOW_TAGS,
    CREATE,
    READ,
    DELETE,
    VALIDATE,
    EXPORT,
)
from .helpers import (
    validate_resume_content,
    format_coverage_report,
    ValidationStats,
)


@tool(
    name="create_job_application",
    tags=RESUME_WORKFLOW_TAGS | {"create"},
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
    tags=RESUME_WORKFLOW_TAGS | {"read"},
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
    tags=RESUME_WORKFLOW_TAGS | {"validate"},
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
    
    validation = validate_resume_content(resume_data, experience_store)
    
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
    result += format_coverage_report(validation.stats)
    
    # Validation result
    result += "\n" + "=" * 60 + "\n"
    if validation.is_valid:
        result += "✅ VALIDATION PASSED\n"
        if validation.message:
            result += f"\n{validation.message}\n"
        result += "\n🎯 NEXT STEP: Call save_tailored_resume() to save this resume.\n"
    else:
        result += "❌ VALIDATION FAILED\n\n"
        result += validation.message + "\n"
        result += "\n⚠️  FIX THE ERRORS ABOVE before calling save_tailored_resume().\n"
        result += "Each work position MUST have at least 3 highlights.\n"
    
    return result


@tool(
    name="save_tailored_resume",
    tags=RESUME_WORKFLOW_TAGS | {"create"},
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
    validation = validate_resume_content(resume_data, experience_store)
    
    if not validation.is_valid:
        result = "❌ RESUME NOT SAVED - VALIDATION FAILED\n" + "=" * 60 + "\n\n"
        result += validation.message + "\n"
        result += format_coverage_report(validation.stats)
        result += "\n⚠️  FIX THE ERRORS ABOVE and try again.\n"
        result += "TIP: Call preview_tailored_resume() first to check your content.\n"
        return result
    
    try:
        path = app_store.save_resume(application_id, resume_data)
        
        result = "✓ TAILORED RESUME SAVED\n" + "=" * 60 + "\n\n"
        result += f"Application: {application_id}\n"
        result += f"File: {path}\n"
        
        # Show coverage stats
        result += format_coverage_report(validation.stats)
        
        # Show warnings if any
        if validation.message:
            result += f"\n{validation.message}\n"
        
        result += "\n🎯 NEXT STEP:\n"
        result += f"Call render_and_compile(application_id='{application_id}') to generate the PDF.\n"
        
        return result
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="render_and_compile",
    tags=RESUME_WORKFLOW_TAGS | {"export"},
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
    tags=APP_TAGS | {"read"},
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
    tags=APP_TAGS | {"read"},
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
    tags=APP_TAGS | {"delete"},
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
    tags=APP_TAGS | {"read"},
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


@tool(
    name="compare_resumes",
    tags=APP_TAGS | {"read"},
    description="""Compare two tailored resumes to show differences.
    
    Useful for understanding how resumes were customized for different jobs
    or for reviewing variations in how you've presented your experience.
    
    Compares:
    - Key highlights
    - Work positions included
    - Highlights per position
    - Skills included
    - Projects included
    
    Args:
        application_id_1: First application ID
        application_id_2: Second application ID
    
    Returns:
        Side-by-side comparison of the two resumes"""
)
def compare_resumes(application_id_1: str, application_id_2: str) -> str:
    """Compare two tailored resumes to show differences."""
    app_store = ApplicationStore()
    
    try:
        resume_1 = app_store.load_resume(application_id_1)
        resume_2 = app_store.load_resume(application_id_2)
    except Exception as e:
        return f"❌ ERROR loading resumes: {str(e)}"
    
    if resume_1 is None:
        return f"❌ No resume found for: {application_id_1}"
    if resume_2 is None:
        return f"❌ No resume found for: {application_id_2}"
    
    result = "📊 RESUME COMPARISON\n" + "=" * 70 + "\n\n"
    result += f"📁 Resume 1: {application_id_1}\n"
    result += f"📁 Resume 2: {application_id_2}\n\n"
    
    # Compare key highlights
    key_highlights_1 = resume_1.get("keyHighlights", [])
    key_highlights_2 = resume_2.get("keyHighlights", [])
    
    result += "-" * 70 + "\n"
    result += "🌟 KEY HIGHLIGHTS\n"
    result += "-" * 70 + "\n"
    result += f"Resume 1: {len(key_highlights_1)} | Resume 2: {len(key_highlights_2)}\n\n"
    
    # Find unique highlights
    set_1 = set(key_highlights_1)
    set_2 = set(key_highlights_2)
    common = set_1 & set_2
    only_in_1 = set_1 - set_2
    only_in_2 = set_2 - set_1
    
    if common:
        result += f"  ✓ Common ({len(common)}):\n"
        for h in list(common)[:3]:
            result += f"    • {h[:70]}...\n" if len(h) > 70 else f"    • {h}\n"
    
    if only_in_1:
        result += f"\n  📁 Only in Resume 1 ({len(only_in_1)}):\n"
        for h in list(only_in_1)[:3]:
            result += f"    • {h[:70]}...\n" if len(h) > 70 else f"    • {h}\n"
    
    if only_in_2:
        result += f"\n  📁 Only in Resume 2 ({len(only_in_2)}):\n"
        for h in list(only_in_2)[:3]:
            result += f"    • {h[:70]}...\n" if len(h) > 70 else f"    • {h}\n"
    
    # Compare work positions
    work_1 = resume_1.get("work", [])
    work_2 = resume_2.get("work", [])
    
    result += "\n" + "-" * 70 + "\n"
    result += "💼 WORK POSITIONS\n"
    result += "-" * 70 + "\n"
    result += f"Resume 1: {len(work_1)} positions | Resume 2: {len(work_2)} positions\n\n"
    
    # Create position keys for comparison
    positions_1 = {f"{w.get('position', '')} at {w.get('name', '')}": w for w in work_1}
    positions_2 = {f"{w.get('position', '')} at {w.get('name', '')}": w for w in work_2}
    
    all_positions = set(positions_1.keys()) | set(positions_2.keys())
    
    for pos in sorted(all_positions):
        in_1 = pos in positions_1
        in_2 = pos in positions_2
        
        h1 = len(positions_1[pos].get("highlights", [])) if in_1 else 0
        h2 = len(positions_2[pos].get("highlights", [])) if in_2 else 0
        
        if in_1 and in_2:
            diff = "=" if h1 == h2 else (f"+{h2-h1}" if h2 > h1 else f"{h2-h1}")
            result += f"  ✓ {pos}\n"
            result += f"      Highlights: {h1} vs {h2} ({diff})\n"
        elif in_1:
            result += f"  📁1 {pos} ({h1} highlights) - Only in Resume 1\n"
        else:
            result += f"  📁2 {pos} ({h2} highlights) - Only in Resume 2\n"
    
    # Compare skills
    skills_1 = resume_1.get("skills", [])
    skills_2 = resume_2.get("skills", [])
    
    result += "\n" + "-" * 70 + "\n"
    result += "🔧 SKILLS\n"
    result += "-" * 70 + "\n"
    result += f"Resume 1: {len(skills_1)} categories | Resume 2: {len(skills_2)} categories\n\n"
    
    cats_1 = {s.get("name", ""): s.get("keywords", []) for s in skills_1}
    cats_2 = {s.get("name", ""): s.get("keywords", []) for s in skills_2}
    
    all_cats = set(cats_1.keys()) | set(cats_2.keys())
    
    for cat in sorted(all_cats):
        kw_1 = set(cats_1.get(cat, []))
        kw_2 = set(cats_2.get(cat, []))
        
        if kw_1 == kw_2:
            result += f"  = {cat}: {len(kw_1)} keywords (identical)\n"
        else:
            common_kw = kw_1 & kw_2
            only_1 = kw_1 - kw_2
            only_2 = kw_2 - kw_1
            result += f"  ≠ {cat}:\n"
            if common_kw:
                result += f"      Common: {len(common_kw)}\n"
            if only_1:
                result += f"      Only R1: {', '.join(list(only_1)[:5])}\n"
            if only_2:
                result += f"      Only R2: {', '.join(list(only_2)[:5])}\n"
    
    # Compare projects
    projects_1 = resume_1.get("projects", [])
    projects_2 = resume_2.get("projects", [])
    
    result += "\n" + "-" * 70 + "\n"
    result += "📂 PROJECTS\n"
    result += "-" * 70 + "\n"
    result += f"Resume 1: {len(projects_1)} | Resume 2: {len(projects_2)}\n"
    
    proj_names_1 = {p.get("name", "") for p in projects_1}
    proj_names_2 = {p.get("name", "") for p in projects_2}
    
    common_proj = proj_names_1 & proj_names_2
    only_proj_1 = proj_names_1 - proj_names_2
    only_proj_2 = proj_names_2 - proj_names_1
    
    if common_proj:
        result += f"\n  ✓ Common: {', '.join(common_proj)}\n"
    if only_proj_1:
        result += f"  📁1 Only in R1: {', '.join(only_proj_1)}\n"
    if only_proj_2:
        result += f"  📁2 Only in R2: {', '.join(only_proj_2)}\n"
    
    # Summary stats
    result += "\n" + "=" * 70 + "\n"
    result += "📈 SUMMARY\n"
    result += "=" * 70 + "\n"
    
    total_highlights_1 = sum(len(w.get("highlights", [])) for w in work_1)
    total_highlights_2 = sum(len(w.get("highlights", [])) for w in work_2)
    total_skills_1 = sum(len(s.get("keywords", [])) for s in skills_1)
    total_skills_2 = sum(len(s.get("keywords", [])) for s in skills_2)
    
    result += f"\n| Metric           | Resume 1 | Resume 2 | Diff    |\n"
    result += f"|------------------|----------|----------|---------||\n"
    result += f"| Key Highlights   | {len(key_highlights_1):>8} | {len(key_highlights_2):>8} | {len(key_highlights_2)-len(key_highlights_1):>+7} |\n"
    result += f"| Work Positions   | {len(work_1):>8} | {len(work_2):>8} | {len(work_2)-len(work_1):>+7} |\n"
    result += f"| Total Highlights | {total_highlights_1:>8} | {total_highlights_2:>8} | {total_highlights_2-total_highlights_1:>+7} |\n"
    result += f"| Skill Categories | {len(skills_1):>8} | {len(skills_2):>8} | {len(skills_2)-len(skills_1):>+7} |\n"
    result += f"| Total Skills     | {total_skills_1:>8} | {total_skills_2:>8} | {total_skills_2-total_skills_1:>+7} |\n"
    result += f"| Projects         | {len(projects_1):>8} | {len(projects_2):>8} | {len(projects_2)-len(projects_1):>+7} |\n"
    
    return result


@tool(
    name="generate_cover_letter_data",
    tags=COVER_LETTER_TAGS | {"create"},
    description="""Generate structured data for a cover letter based on job and experience match.
    
    Analyzes the job description and your tailored resume to identify:
    - Key matching points between your experience and the job
    - Unique value propositions you bring
    - Specific examples to highlight
    - Suggested opening and closing hooks
    
    This provides the raw material for crafting a compelling cover letter.
    
    Args:
        application_id: The application ID (must have a saved resume)
    
    Returns:
        Structured cover letter data with talking points and suggestions"""
)
def generate_cover_letter_data(application_id: str) -> str:
    """Generate structured data for cover letter creation."""
    import json
    from pathlib import Path
    
    app_store = ApplicationStore()
    
    # Load the application details
    try:
        app = app_store.get_application(application_id)
    except FileNotFoundError:
        return f"❌ Application not found: {application_id}"
    except Exception as e:
        return f"❌ Error loading application: {str(e)}"
    
    # Load the tailored resume
    try:
        resume = app_store.load_resume(application_id)
    except Exception as e:
        return f"❌ Error loading resume: {str(e)}"
    
    if resume is None:
        return f"❌ No resume found for application: {application_id}\n\nGenerate a tailored resume first using save_tailored_resume()."
    
    # Load the job description
    app_folder = app_store.storage_paths.output_folder / application_id
    jd_file = app_folder / "job_description.txt"
    
    job_description = ""
    if jd_file.exists():
        job_description = jd_file.read_text()
    
    result = "✉️ COVER LETTER DATA\n" + "=" * 70 + "\n\n"
    result += f"📁 Application: {application_id}\n"
    
    # Extract basics
    basics = resume.get("basics", {})
    result += f"👤 Candidate: {basics.get('name', 'N/A')}\n"
    result += f"📧 Email: {basics.get('email', 'N/A')}\n\n"
    
    # Parse company and position from application_id
    parts = application_id.split("_", 1)
    company = parts[0] if parts else "the company"
    position = parts[1].replace("_", " ") if len(parts) > 1 else "this position"
    
    result += "-" * 70 + "\n"
    result += "🎯 KEY MATCHING POINTS\n"
    result += "-" * 70 + "\n"
    result += "These are the strongest connections between your experience and the job:\n\n"
    
    # Key highlights are the best matches
    key_highlights = resume.get("keyHighlights", [])
    if key_highlights:
        for i, highlight in enumerate(key_highlights[:5], 1):
            result += f"{i}. {highlight}\n"
    else:
        result += "  (No key highlights found - add them to your resume)\n"
    
    # Extract top work positions with most highlights
    result += "\n" + "-" * 70 + "\n"
    result += "💼 RELEVANT EXPERIENCE TO EMPHASIZE\n"
    result += "-" * 70 + "\n"
    
    work = resume.get("work", [])
    sorted_work = sorted(work, key=lambda w: len(w.get("highlights", [])), reverse=True)
    
    for pos in sorted_work[:3]:
        pos_name = pos.get("position", "Position")
        company_name = pos.get("name", "Company")
        highlights = pos.get("highlights", [])
        
        result += f"\n📌 {pos_name} at {company_name}\n"
        result += f"   Best talking points:\n"
        for h in highlights[:2]:
            result += f"   • {h[:100]}{'...' if len(h) > 100 else ''}\n"
    
    # Skills that match
    result += "\n" + "-" * 70 + "\n"
    result += "🔧 SKILLS TO HIGHLIGHT\n"
    result += "-" * 70 + "\n"
    
    skills = resume.get("skills", [])
    all_keywords = []
    for skill in skills:
        all_keywords.extend(skill.get("keywords", []))
    
    if all_keywords:
        result += "Mention these naturally in your letter:\n"
        result += "  " + ", ".join(all_keywords[:15])
        if len(all_keywords) > 15:
            result += f" (+{len(all_keywords) - 15} more)"
        result += "\n"
    
    # Projects to mention
    projects = resume.get("projects", [])
    if projects:
        result += "\n" + "-" * 70 + "\n"
        result += "📂 PROJECTS TO SHOWCASE\n"
        result += "-" * 70 + "\n"
        
        for proj in projects[:2]:
            proj_name = proj.get("name", "Project")
            proj_desc = proj.get("description", "")[:100]
            result += f"• {proj_name}: {proj_desc}...\n"
    
    # Suggested structure
    result += "\n" + "=" * 70 + "\n"
    result += "📝 SUGGESTED LETTER STRUCTURE\n"
    result += "=" * 70 + "\n"
    
    result += """
1. OPENING HOOK (1-2 sentences)
   - Lead with your most impressive relevant achievement
   - Connect it to why you're excited about this role
   
   Example: "Having [key achievement], I'm excited about the opportunity to
   bring this experience to [company] as a [position]."

2. WHY THIS COMPANY (1 paragraph)
   - What specifically attracts you to the company
   - How their mission/product aligns with your interests
   - Reference something specific (recent news, product, values)

3. VALUE PROPOSITION (2 paragraphs)
   - Paragraph 1: Your most relevant experience
     • Choose 1-2 key highlights that directly match the JD
     • Use specific metrics and outcomes
   - Paragraph 2: Unique qualities you bring
     • What differentiates you from other candidates
     • Soft skills or perspectives that add value

4. CLOSING (1 paragraph)
   - Reiterate enthusiasm
   - Call to action
   - Thank them for consideration

"""

    # Word count targets
    result += "-" * 70 + "\n"
    result += "📏 GUIDELINES\n"
    result += "-" * 70 + "\n"
    result += "• Length: 250-400 words (one page max)\n"
    result += "• Tone: Professional but personable\n"
    result += "• Avoid: Repeating resume bullet points verbatim\n"
    result += "• Focus: Why you + why this company = great fit\n"
    
    return result


@tool(
    name="save_cover_letter",
    tags=COVER_LETTER_TAGS | {"create"},
    description="""Save a cover letter to an application folder.
    
    Args:
        application_id: The application ID
        cover_letter_content: The cover letter text content
    
    Returns:
        Confirmation with file path"""
)
def save_cover_letter(application_id: str, cover_letter_content: str) -> str:
    """Save a cover letter to the application folder."""
    app_store = ApplicationStore()
    
    # Verify application exists
    try:
        app = app_store.get_application(application_id)
    except FileNotFoundError:
        return f"❌ Application not found: {application_id}"
    
    # Save the cover letter
    app_folder = app_store.storage_paths.output_folder / application_id
    cover_letter_file = app_folder / "cover_letter.txt"
    
    try:
        cover_letter_file.write_text(cover_letter_content)
    except Exception as e:
        return f"❌ Error saving cover letter: {str(e)}"
    
    word_count = len(cover_letter_content.split())
    
    result = f"✅ COVER LETTER SAVED\n" + "=" * 60 + "\n\n"
    result += f"📁 Application: {application_id}\n"
    result += f"📄 File: {cover_letter_file}\n"
    result += f"📊 Word count: {word_count}\n\n"
    
    if word_count < 200:
        result += "⚠️  Cover letter may be too short (< 200 words)\n"
    elif word_count > 500:
        result += "⚠️  Cover letter may be too long (> 500 words)\n"
    else:
        result += "✓ Length looks good!\n"
    
    # List all application files
    result += "\n📂 Application files:\n"
    for f in sorted(app_folder.iterdir()):
        if f.is_file():
            result += f"   • {f.name}\n"
    
    return result


@tool(
    name="get_cover_letter",
    tags=COVER_LETTER_TAGS | {"read"},
    description="""Get the cover letter from an application.
    
    Args:
        application_id: The application ID
    
    Returns:
        The cover letter content or a message if not found"""
)
def get_cover_letter(application_id: str) -> str:
    """Get the cover letter from an application folder."""
    app_store = ApplicationStore()
    
    # Verify application exists
    try:
        app = app_store.get_application(application_id)
    except FileNotFoundError:
        return f"❌ Application not found: {application_id}"
    
    app_folder = app_store.storage_paths.output_folder / application_id
    cover_letter_file = app_folder / "cover_letter.txt"
    
    if not cover_letter_file.exists():
        return f"❌ No cover letter found for: {application_id}\n\nGenerate one using generate_cover_letter_data() first, then save with save_cover_letter()."
    
    content = cover_letter_file.read_text()
    word_count = len(content.split())
    
    result = f"✉️ COVER LETTER: {application_id}\n" + "=" * 60 + "\n"
    result += f"📊 Word count: {word_count}\n\n"
    result += content
    
    return result
