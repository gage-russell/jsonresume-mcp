from fastmcp import FastMCP

from resumejson_mcp.mcp.setup.v1 import tools as setup_tools
from resumejson_mcp.mcp.experience.v1.work import tools as work_tools
from resumejson_mcp.mcp.experience.v1.projects import tools as project_tools
from resumejson_mcp.mcp.experience.v1.education import tools as education_tools
from resumejson_mcp.mcp.experience.v1.skills import tools as skill_tools
from resumejson_mcp.mcp.experience.v1.basics import tools as basics_tools
from resumejson_mcp.mcp.templates.v1 import tools as template_tools
from resumejson_mcp.mcp.applications.v1 import tools as application_tools


mcp = FastMCP(
    name="ResumeJSON-MCP",
    instructions="""
        This server provides tools for managing JSON Resume data with MCP extensions
        and generating tailored resumes for job applications.
        
        FIRST TIME SETUP:
        1. Run check_setup_status() to verify configuration
        2. If not configured, run setup_storage() to initialize directories
        3. Run initialize_experience() to create your experience.json file
        4. Start adding work experience with add_work()
        
        ============================================================================
        CORE WORKFLOW: GENERATING TAILORED RESUMES
        ============================================================================
        
        1. USER PROVIDES JOB DESCRIPTION
           → Call create_job_application(company, position, job_description)
           → Creates folder with job_description.txt
        
        2. AI GENERATES TAILORED RESUME
           → Call get_experience_for_tailoring() to get full experience data
           → Analyze job description and select relevant content:
             * Pick best 3-5 bullets per work position
             * Select matching skills
             * Choose relevant projects
           → Craft tailored highlights (rewrite bullets to match JD keywords)
           → Build a clean JSON Resume dict (NO mcp-details)
        
        3. SAVE AND COMPILE
           → Call save_tailored_resume(application_id, resume_data)
           → Call render_and_compile(application_id) to generate PDF
        
        ============================================================================
        DATA STRUCTURE
        ============================================================================
        
        experience.json (stored in experience_folder):
        - Comprehensive career data with mcp-details
        - Used as SOURCE for generating tailored resumes
        - Contains: basics, work, education, skills, projects
        
        resume.json (in each application folder):
        - Clean JSON Resume spec (NO mcp-details)
        - Contains: basics, work, education, skills, projects
        - work[].highlights = tailored bullet points
        
        ============================================================================
        MCP-DETAILS FIELDS (experience.json only)
        ============================================================================
        
        Each section can include mcp-details with:
        - id: Unique identifier (required)
        - bullets: List of accomplishment/responsibility bullet points (for work)
        - major_projects: Detailed project context for resume generation (for work)
        - tags: Keywords for job matching and filtering
        
        CRITICAL: mcp-details are for STORAGE only. They help the AI understand
        context and generate tailored content. They should NOT appear in the
        final resume.json output.
        
        ============================================================================
        IMPORTANT GUIDELINES
        ============================================================================
        
        - ALWAYS extract and populate bullets and major projects when adding work
        - INFER accomplishments from user descriptions - don't wait for explicit lists
        - Ask follow-up questions to gather complete information
        - Minimum 2-3 bullets and 1-2 major projects per work position
        - When tailoring: prioritize keywords from the job description
        - Rewrite bullets to emphasize relevant skills for the target role
    """,
)

# Setup tools
mcp.add_prompt(setup_tools.setup_storage_prompt)
mcp.add_tool(setup_tools.setup_storage)
mcp.add_tool(setup_tools.initialize_experience)
mcp.add_tool(setup_tools.check_setup_status)
mcp.add_resource(setup_tools.get_storage_paths)

# Basics tools
mcp.add_tool(basics_tools.get_basics)
mcp.add_tool(basics_tools.set_basics)

# Work tools
mcp.add_tool(work_tools.get_all_work)
mcp.add_tool(work_tools.get_work_by_id)
mcp.add_tool(work_tools.add_work)
mcp.add_tool(work_tools.update_work)
mcp.add_tool(work_tools.delete_work)
mcp.add_tool(work_tools.add_bullet_to_work)
mcp.add_tool(work_tools.add_major_project_to_work)

# Education tools
mcp.add_tool(education_tools.get_all_education)
mcp.add_tool(education_tools.get_education_by_id)
mcp.add_tool(education_tools.add_education)
mcp.add_tool(education_tools.update_education)
mcp.add_tool(education_tools.delete_education)

# Skills tools
mcp.add_tool(skill_tools.get_all_skills)
mcp.add_tool(skill_tools.get_skill_by_id)
mcp.add_tool(skill_tools.add_skill)
mcp.add_tool(skill_tools.add_skills)
mcp.add_tool(skill_tools.update_skill)
mcp.add_tool(skill_tools.delete_skill)

# Project tools
mcp.add_tool(project_tools.get_all_projects)
mcp.add_tool(project_tools.get_project_by_id)
mcp.add_tool(project_tools.add_project)
mcp.add_tool(project_tools.add_projects)
mcp.add_tool(project_tools.update_project)
mcp.add_tool(project_tools.delete_project)

# Template tools
mcp.add_tool(template_tools.list_templates)
mcp.add_tool(template_tools.get_template_content)
mcp.add_tool(template_tools.create_template)
mcp.add_tool(template_tools.update_template)
mcp.add_tool(template_tools.delete_template)
mcp.add_tool(template_tools.render_resume)
mcp.add_tool(template_tools.preview_render)

# Application tools (job application workflow)
mcp.add_tool(application_tools.create_job_application)
mcp.add_tool(application_tools.get_experience_for_tailoring)
mcp.add_tool(application_tools.save_tailored_resume)
mcp.add_tool(application_tools.render_and_compile)
mcp.add_tool(application_tools.list_applications)
mcp.add_tool(application_tools.get_application)
mcp.add_tool(application_tools.get_application_resume)
mcp.add_tool(application_tools.delete_application)


if __name__ == "__main__":
    mcp.run()
