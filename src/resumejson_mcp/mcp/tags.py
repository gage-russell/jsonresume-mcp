"""Centralized tag constants for MCP tool categorization.

All tool tags should be defined here to:
1. Avoid duplication across tool modules
2. Make it easy to see which tools share tags (for co-activation)
3. Enable consistent naming conventions

Tag naming conventions:
- Use lowercase with hyphens for multi-word tags
- Category tags: broad groupings (e.g., "experience", "applications")
- Action tags: CRUD operations (e.g., "create", "read", "update", "delete")
- Workflow tags: multi-tool workflows that should activate together
"""

# =============================================================================
# CATEGORY TAGS - Broad groupings
# =============================================================================

EXPERIENCE = "experience"
APPLICATIONS = "applications"
WORKFLOW = "workflow"
TEMPLATES = "templates"
SETUP = "setup"

# =============================================================================
# ENTITY TAGS - Specific data entities
# =============================================================================

WORK = "work"
SKILLS = "skills"
PROJECTS = "projects"
EDUCATION = "education"
BASICS = "basics"
BULLETS = "bullets"
COVER_LETTER = "cover-letter"

# =============================================================================
# ACTION TAGS - CRUD operations
# =============================================================================

CREATE = "create"
READ = "read"
UPDATE = "update"
DELETE = "delete"
LIST = "list"
BULK = "bulk"
EXPORT = "export"
VALIDATE = "validate"
ANALYZE = "analyze"

# =============================================================================
# WORKFLOW TAGS - Tools that should activate together
# =============================================================================

RESUME_WORKFLOW = "resume-workflow"
TODOS = "todos"
RESEARCH = "research"

# =============================================================================
# COMPOSITE TAG SETS - Pre-defined combinations for common tool types
# =============================================================================

# Experience management tools
EXPERIENCE_TAGS = frozenset({EXPERIENCE})
WORK_TAGS = frozenset({EXPERIENCE, WORK})
SKILLS_TAGS = frozenset({EXPERIENCE, SKILLS})
PROJECTS_TAGS = frozenset({EXPERIENCE, PROJECTS})
EDUCATION_TAGS = frozenset({EXPERIENCE, EDUCATION})
BASICS_TAGS = frozenset({EXPERIENCE, BASICS})

# Application workflow tools (these activate together)
APP_TAGS = frozenset({APPLICATIONS})
RESUME_WORKFLOW_TAGS = frozenset({APPLICATIONS, RESUME_WORKFLOW})
COVER_LETTER_TAGS = frozenset({APPLICATIONS, COVER_LETTER})

# Workflow management tools
WORKFLOW_TAGS = frozenset({WORKFLOW})
TODO_TAGS = frozenset({WORKFLOW, TODOS})
ANALYZE_TAGS = frozenset({WORKFLOW, ANALYZE, RESUME_WORKFLOW})

# Validation and backup tools
VALIDATE_TAGS = frozenset({SETUP, VALIDATE})
BACKUP_TAGS = frozenset({SETUP, "backup"})
EXPORT_TAGS = frozenset({EXPERIENCE, EXPORT})

# Setup and configuration tools
SETUP_TAGS = frozenset({SETUP, CREATE})
TEMPLATES_TAGS = frozenset({TEMPLATES})
