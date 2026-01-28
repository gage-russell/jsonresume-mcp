"""MCP tools for managing job applications."""

from fastmcp.tools import tool

from resumejson_mcp.lib.applications.application_store import ApplicationStore
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Resume


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
    
    Use this data to select and craft tailored content for a specific job.
    
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
    name="save_tailored_resume",
    description="""Save a tailored resume to an application folder.
    
    The resume_data should be a clean JSON Resume object with:
    - basics: Contact information
    - work: Selected positions with tailored highlights (NOT mcp-details)
    - skills: Selected relevant skills
    - projects: Selected relevant projects
    - education: Education entries
    
    DO NOT include mcp-details fields - they will be stripped automatically.
    The work[].highlights should contain the tailored bullet points.
    
    Args:
        application_id: The application ID from create_job_application
        resume_data: The tailored resume as a dict (JSON Resume format)
        
    Returns:
        Success message with file path"""
)
def save_tailored_resume(application_id: str, resume_data: dict) -> str:
    app_store = ApplicationStore()
    
    try:
        path = app_store.save_resume(application_id, resume_data)
        
        result = "✓ TAILORED RESUME SAVED\n" + "=" * 60 + "\n\n"
        result += f"Application: {application_id}\n"
        result += f"File: {path}\n"
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
            result += f"📄 Open PDF: file://{pdf_path}\n"
            result += f"📂 Folder: file://{pdf_path.parent}\n"
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
