from fastmcp import FastMCP

from resumejson_mcp.mcp.setup.v1 import tools as setup_tools
from resumejson_mcp.mcp.experience.v1.work import tools as work_tools
from resumejson_mcp.mcp.experience.v1.projects import tools as project_tools
from resumejson_mcp.mcp.experience.v1.education import tools as education_tools
from resumejson_mcp.mcp.experience.v1.skills import tools as skill_tools
from resumejson_mcp.mcp.experience.v1.basics import tools as basics_tools


mcp = FastMCP(
    name="ResumeJSON-MCP",
    instructions="""
        This server provides tools for managing JSON Resume data with MCP extensions.
        
        FIRST TIME SETUP:
        1. Run check_setup_status() to verify configuration
        2. If not configured, run setup_storage() to initialize directories
        3. Run initialize_experience() to create your experience.json file
        4. Start adding work experience with add_work()
        
        OVERVIEW:
        The system stores comprehensive career experience data following the JSON Resume schema
        with MCP extensions. Data is stored in a single experience.json file and can be used
        to generate tailored resumes for specific job applications.
        
        DATA STRUCTURE:
        - Basics: Personal information (name, email, phone, location, profiles, summary) - use get/set basics tools
        - Work: Work experience with nested bullets and major projects - use add/update/delete work tools
        - Education: Degrees and institutions - use add/update/delete education tools
        - Skills: Individual skills organized by category - use add/update/delete skill tools
        - Projects: Portfolio/showcase projects - use add/update/delete project tools
        
        CRITICAL DISTINCTION - TWO TYPES OF PROJECTS:
        
        1. work[].mcp_details.major_projects (use add_major_project_to_work):
           - Contextual information about projects done at a specific job
           - Helps AI understand work deeply to generate tailored resume bullets
           - NOT displayed directly on resumes
           - Used by AI to create targeted highlights for job applications
        
        2. Top-level projects (use add_project):
           - Portfolio/showcase projects that appear directly on resumes
           - E.g., GitHub repos, side projects, open source contributions
           - Have their own highlights that appear on the resume
           - Separate from work experience
        
        MCP EXTENSIONS:
        Each section can include mcp-details with:
        - id: Unique identifier (required)
        - bullets: List of accomplishment/responsibility bullet points (for work)
        - major_projects: Detailed project context for resume generation (for work)
        - tags: Keywords for job matching and filtering
        
        WORKFLOW FOR ADDING EXPERIENCE:
        1. Add work positions with bullets and major_projects using add_work
        2. Add education background using add_education
        3. Add portfolio projects using add_project
        4. Add skills mentioned in the work/projects (coming soon)
        
        IMPORTANT GUIDELINES:
        - ALWAYS extract and populate bullets and major projects when adding work
        - INFER accomplishments from user descriptions - don't wait for explicit lists
        - Ask follow-up questions to gather complete information
        - Minimum 2-3 bullets and 1-2 major projects per work position
        - If user mentions side projects/GitHub repos, use add_project (NOT add_major_project_to_work)
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


if __name__ == "__main__":
    mcp.run()
