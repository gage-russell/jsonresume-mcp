"""
Interactive prompts for ResumeJSON-MCP workflows.

These prompts guide users through common multi-step workflows
like gathering work experience or tailoring resumes for specific jobs.
"""


def gather_work_experience_prompt() -> str:
    """Return a prompt template for gathering work experience."""
    return """# Gather Work Experience

I'll help you document a work position for your resume. Let's gather all the details.

## Step 1: Basic Position Info

Please provide:
1. **Company Name**: 
2. **Your Job Title**: 
3. **Location** (City, State/Country): 
4. **Start Date** (YYYY-MM): 
5. **End Date** (YYYY-MM or "Present"): 
6. **Brief Summary** (1-2 sentences about the role): 

## Step 2: Key Accomplishments

Now let's capture your achievements. For each accomplishment, think about:
- **What did you do?** (Action verb)
- **How did you do it?** (Tools, methods, technologies)
- **What was the result?** (Metrics, impact, outcomes)

Template: "**[Action verb]** [what you did] using [how], resulting in [quantified impact]"

Examples:
- "Designed and implemented a distributed caching layer using Redis, reducing API latency by 40%"
- "Led migration of 50+ microservices to Kubernetes, achieving 99.99% uptime"
- "Mentored team of 5 junior engineers, with 3 receiving promotions within 18 months"

**Please share 3-5 key accomplishments:**

1. 
2. 
3. 
4. 
5. 

## Step 3: Major Projects

What were 1-2 significant projects you worked on? For each project:

### Project 1:
- **Name**: 
- **Summary** (What was it? What was your role?): 
- **Technologies Used**: 
- **Challenges & How You Solved Them**: 
- **Outcomes/Impact**: 
- **Team Context** (Team size, your specific contributions): 

### Project 2 (optional):
- **Name**: 
- **Summary**: 
- **Technologies Used**: 
- **Challenges & How You Solved Them**: 
- **Outcomes/Impact**: 

## Step 4: Skills & Tags

What technologies, skills, and domains were involved? (These help with job matching)

**Technical Skills**: (e.g., Python, AWS, Kubernetes, PostgreSQL)
**Domains**: (e.g., data-engineering, platform, backend, frontend)
**Achievements**: (e.g., cost-savings, performance, leadership)

---

After gathering this information, I will:
1. Create the work position using `add_work()`
2. Add accomplishment bullets with `add_bullets_to_work()`
3. Add major projects with `add_major_project_to_work()`
4. Track any missing information as pending actions

Let's start! What company and position would you like to document?"""


def tailor_resume_for_job_prompt(job_description: str) -> str:
    """Return a prompt template for tailoring a resume."""
    return f"""# Tailor Resume for Job Application

I'll help you create a tailored resume for this position.

## Job Description Provided:
```
{job_description[:2000]}{'...' if len(job_description) > 2000 else ''}
```

---

## Tailoring Workflow

### Step 1: Analyze the Job Description

First, I'll use `analyze_job_description()` to extract:
- Required skills and technologies
- Key responsibilities and action words
- Experience level requirements
- Nice-to-have qualifications
- Keywords for ATS optimization

### Step 2: Create Application Folder

I'll use `create_job_application()` to set up the application folder with:
- Company name and position
- The full job description for reference

### Step 3: Review Your Experience

I'll use `get_experience_for_tailoring()` to pull your complete experience data.

### Step 4: Match Experience to Requirements

For each job requirement, I'll identify:
- ✅ **Strong matches**: Bullets that directly address the requirement
- 🔶 **Partial matches**: Experience that's related but needs emphasis
- ❌ **Gaps**: Requirements you may not have (can address in cover letter)

### Step 5: Select & Prioritize Content

**Key Highlights** (3-5): Your top achievements that match this role
**Work Positions**: Which positions to include and bullet priority
**Skills**: Relevant skill categories that match the JD
**Projects**: Portfolio projects that demonstrate required capabilities

### Step 6: Craft the Tailored Resume

Using `preview_tailored_resume()` to validate:
- Minimum 4-5 highlights per position
- 70%+ position coverage
- 60%+ bullet coverage
- Key skills represented

### Step 7: Save & Render

Using `save_tailored_resume()` and `render_and_compile()` to generate the final PDF.

---

## Ready to Begin?

Shall I start by analyzing this job description? I'll walk you through each step.
"""


def quick_resume_update_prompt() -> str:
    """Return a prompt for quick resume updates."""
    return """# Quick Resume Update

Let me help you update your resume quickly.

## What would you like to update?

1. **Add new accomplishments** to an existing position
2. **Add a new job position**
3. **Add a new project** to your portfolio
4. **Update contact information**
5. **Add new skills**

## Quick Commands

| Update Type | Command to Use |
|-------------|----------------|
| New accomplishment | `add_bullet_to_work(work_id, bullet)` |
| Multiple accomplishments | `add_bullets_to_work(work_id, bullets)` |
| New position | `add_work(work)` |
| New project | `add_project(project)` |
| Contact info | `update_basics_field(field, value)` |
| New skill | `add_skill(skill)` |

## Tips for Strong Bullets

Remember the **STAR+Metrics** format:
- **S**ituation: Context or challenge
- **T**ask: Your responsibility
- **A**ction: What you did (strong verb!)
- **R**esult: Quantified impact

**Strong verbs**: Architected, Designed, Implemented, Led, Optimized, Reduced, 
Increased, Automated, Delivered, Mentored, Migrated, Scaled

**Metrics**: %, $, time saved, users impacted, team size, uptime, latency

---

What would you like to update?"""


def review_experience_quality_prompt() -> str:
    """Return a prompt for reviewing experience quality."""
    return """# Experience Quality Review

Let me help you review and improve your stored experience data.

## Quality Audit Workflow

### Step 1: Get Overview
First, I'll run `get_experience_stats()` to see:
- Total positions, bullets, and projects
- Average bullets per position
- Date coverage
- Tag distribution

### Step 2: Validate Data
Next, I'll run `validate_experience()` to check:
- Missing required fields
- Duplicate IDs
- Date format consistency
- Orphaned references

### Step 3: Position-by-Position Review
For each work position, I'll use `validate_work_position()` to get a quality grade:
- **A**: Excellent - Ready for any application
- **B**: Good - Minor improvements possible
- **C**: Fair - Needs more accomplishments or metrics
- **D**: Poor - Missing critical information
- **F**: Failing - Significant gaps

### Step 4: Recommendations
I'll provide specific recommendations:
- Bullets that need metrics added
- Positions missing major projects
- Skills that should be tagged
- Accomplishments to add

### Step 5: Action Plan
We'll create a prioritized list of improvements:
1. Critical fixes (missing required data)
2. High-value additions (metrics, outcomes)
3. Nice-to-have polish (better wording)

---

Shall I start the quality review? I'll give you a complete assessment of your experience data."""


def first_time_setup_prompt() -> str:
    """Return a prompt for first-time setup."""
    return """# Welcome to ResumeJSON-MCP! 🎉

I'll help you set up your resume management system.

## What is ResumeJSON-MCP?

A system for:
- 📝 **Storing** your complete career experience in one place
- 🎯 **Tailoring** resumes for specific job applications
- 📄 **Generating** professional PDF resumes from LaTeX templates

## Setup Steps

### Step 1: Initialize Storage
First, we'll set up your data directories:
```
~/.hire-me/
├── experience/           # Your career data
│   ├── experience.json   # All your experience
│   └── .backups/         # Automatic backups
└── applications/         # Job applications
    └── {company}_{role}/ # Each application
```

I'll use `setup_storage()` and `initialize_experience()`.

### Step 2: Add Contact Information
Let's add your basic info:
- Name, email, phone
- Location
- LinkedIn, GitHub, website
- Professional summary

I'll use `set_basics()`.

### Step 3: Add Work Experience
For each position, we'll capture:
- Company, title, dates
- Key accomplishments (as bullets)
- Major projects with context
- Technologies and skills used

I'll use `add_work()`, `add_bullets_to_work()`, `add_major_project_to_work()`.

### Step 4: Add Skills
Organize your skills by category:
- Languages: Python, JavaScript, Go...
- Frameworks: React, Django, FastAPI...
- Tools: Docker, Kubernetes, Terraform...
- Databases: PostgreSQL, Redis, MongoDB...

I'll use `add_skills()`.

### Step 5: Add Portfolio Projects (Optional)
Showcase side projects, open source, or notable work:
- Project name and description
- Technologies used
- Your role and contributions
- Links (GitHub, demo, etc.)

I'll use `add_project()`.

---

## Ready to Begin?

Let's start with Step 1. Shall I initialize your storage directories?

After setup, you can:
- `get_experience_stats()` - View your data summary
- `create_job_application()` - Start tailoring for a job
- `validate_experience()` - Check data quality

What would you like to do first?"""
