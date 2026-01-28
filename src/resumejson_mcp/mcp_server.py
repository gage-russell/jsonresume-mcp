from fastmcp import FastMCP

from resumejson_mcp.mcp.setup.v1 import tools as setup_tools
from resumejson_mcp.mcp.experience.v1.work import tools as work_tools
from resumejson_mcp.mcp.experience.v1.projects import tools as project_tools
from resumejson_mcp.mcp.experience.v1.education import tools as education_tools
from resumejson_mcp.mcp.experience.v1.skills import tools as skill_tools
from resumejson_mcp.mcp.experience.v1.basics import tools as basics_tools
from resumejson_mcp.mcp.templates.v1 import tools as template_tools
from resumejson_mcp.mcp.applications.v1 import tools as application_tools
from resumejson_mcp.mcp.workflow.v1 import tools as workflow_tools


mcp = FastMCP(
    name="ResumeJSON-MCP",
    instructions="""
        This server provides tools for managing JSON Resume data with MCP extensions
        and generating tailored resumes for job applications.
        
        ============================================================================
        ⚠️  CRITICAL: PENDING ACTIONS WORKFLOW
        ============================================================================
        
        This server tracks PENDING ACTIONS that you must complete. After any operation
        that creates pending actions (e.g., add_work), you will see a summary like:
        
            📋 PENDING ACTIONS (DO NOT SKIP):
            🔴 CRITICAL: Add accomplishment bullets to: Senior Engineer at Acme
            🟠 HIGH: Add skills: Python, Kubernetes, Kafka (+5 more)
        
        YOU MUST:
        1. Complete all CRITICAL actions before moving on
        2. Complete HIGH priority actions in the same session
        3. Use get_pending_todos() to check your pending work
        4. Use complete_todo(action_id) or complete_todos_of_type(type) to mark done
        
        DO NOT ignore pending actions and move on to new requests.
        
        ============================================================================
        FIRST TIME SETUP
        ============================================================================
        
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
           → Analyze job description requirements and keywords
           
           CRAFTING KEY HIGHLIGHTS (REQUIRED - 3-5):
           Create a "keyHighlights" array with 3-5 TOP achievements that:
             * Directly match the most important job requirements
             * Showcase your strongest, most relevant accomplishments
             * Lead with impact metrics when possible
             * These appear prominently at the top of the resume!
           
           CRAFTING POSITION HIGHLIGHTS - PREFER EXISTING BULLETS:
           The mcp-details.bullets contain WELL-CRAFTED accomplishments.
           
           CRITICAL: Use existing bullets as-is unless you are CERTAIN you can
           improve them. The user has carefully written these bullets.
           
           For each position:
             1. SELECT the most relevant existing bullets from mcp-details.bullets
             2. Use them VERBATIM - do not reword unless clearly necessary
             3. Only rewrite a bullet if:
                - It needs a keyword from the JD that's genuinely missing
                - You can add a specific metric that makes it stronger
                - The original is unclear or poorly written
             4. Use context from major_projects to understand the work,
                but prefer the existing bullet text
           
           WHEN TO MODIFY (rare):
             * Adding a specific keyword that's clearly missing
             * Combining two related bullets into one stronger statement
             * Adding quantification when you know the metric
           
           WHEN NOT TO MODIFY (default):
             * Bullet already captures the accomplishment well
             * You're just changing words to "sound better" - don't
             * You're guessing at metrics you don't actually know
           
           COVERAGE REQUIREMENTS (STRICT):
             * keyHighlights: REQUIRED - 3-5 top achievements for the role
             * Include 70%+ of work positions (most positions should appear!)
             * Each position MUST have 4-5 highlights (not just 3)
             * Aim for 60%+ overall bullet coverage
             * Older/less relevant positions can have 3 highlights minimum
             * Select matching skills and relevant projects
           
           → Build a clean JSON Resume dict (NO mcp-details in output)
        
        3. PREVIEW AND VALIDATE (REQUIRED)
           → Call preview_tailored_resume(resume_data) BEFORE saving
           → Review position-level coverage stats
           → Fix any positions with missing or insufficient highlights
           → Validation MUST pass before saving
        
        4. SAVE AND COMPILE
           → Call save_tailored_resume(application_id, resume_data)
           → Call render_and_compile(application_id) to generate PDF
        
        ============================================================================
        ADDING WORK EXPERIENCE WORKFLOW
        ============================================================================
        
        When adding work with add_work(), the system will automatically:
        1. Track missing bullets as CRITICAL pending action
        2. Track missing major projects as CRITICAL pending action
        3. Extract technologies and track as HIGH priority skill additions
        4. Detect potential portfolio projects as MEDIUM priority
        
        You MUST complete these actions before asking "what's next?"
        
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
mcp.add_tool(application_tools.preview_tailored_resume)
mcp.add_tool(application_tools.save_tailored_resume)
mcp.add_tool(application_tools.render_and_compile)
mcp.add_tool(application_tools.list_applications)
mcp.add_tool(application_tools.get_application)
mcp.add_tool(application_tools.get_application_resume)
mcp.add_tool(application_tools.delete_application)

# Workflow tools (pending actions / todos)
mcp.add_tool(workflow_tools.get_pending_todos)
mcp.add_tool(workflow_tools.complete_todo)
mcp.add_tool(workflow_tools.complete_todos_of_type)
mcp.add_tool(workflow_tools.clear_completed_todos)


if __name__ == "__main__":
    mcp.run()
