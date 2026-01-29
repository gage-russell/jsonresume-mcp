# Tool Consolidation Analysis: Agent-First Design

## The Real Problem: Agent Confusion

The issue isn't just "too many tools" (71). It's that the current design makes it hard for an AI agent to:

1. **Know what tools exist** - 71 tools = cognitive overload, some get disabled by clients
2. **Choose the right tool** - `add_bullet` vs `add_bullets`? Ambiguous.
3. **Execute workflows correctly** - 4 separate tools for one logical action (create → get → save → compile)
4. **Recover from errors** - Tool names don't indicate recovery paths
5. **Sequence actions properly** - No clear workflow stages

---

## Design Principles for Agent-Friendly Tools

1. **One logical action = One tool** (don't split what's always done together)
2. **Names should be verbs that describe the outcome** (`compile_pdf` not `render_and_compile`)
3. **Eliminate ambiguous choices** (no `add_X` AND `add_Xs` - just one that handles both)
4. **Group by workflow stage** (not by data type)
5. **Include recovery hints in descriptions** ("If not found, use X to list available items")
6. **Return useful context** (create_application should return experience data - no second call needed)

---

## Pain Point 1: The Application Workflow is Fragmented

### Current workflow requires 4+ tool calls:
```
1. create_job_application(company, position, job_description)
2. get_experience_for_tailoring()  ← Why is this separate?
3. save_tailored_resume(application_id, resume_data)
4. render_and_compile(application_id)  ← Always called after save
```

**Problems:**
- Agent must know the correct sequence
- Must remember application_id between calls
- 4 round trips for one logical action
- `get_experience_for_tailoring` is always called after `create_job_application`
- `render_and_compile` is always called after `save_tailored_resume`

### Agent-friendly redesign:
```
1. create_application(company, position, job_description)
   → Returns: application_id + full experience data (no separate get needed)

2. save_and_compile(application_id, resume_data, compile=True)
   → Validates, saves, and compiles PDF in one call
```

**Result:** 2 tools instead of 4. Agent can't get sequence wrong.

---

## Pain Point 2: Ambiguous Tool Selection

### Current confusion pairs:
| Tool A | Tool B | Agent's Question |
|--------|--------|------------------|
| `add_bullet_to_work` | `add_bullets_to_work` | "Which one do I use?" |
| `add_skill` | `add_skills` | "Is it one skill or multiple?" |
| `add_project` | `add_projects` | Same confusion |
| `get_application` | `get_application_resume` | "What's the difference?" |
| `preview_render` | `preview_template_with_sample_data` | Same name pattern, different purpose |
| `validate_experience` | `validate_work_position` | "Which validation do I need?" |
| `complete_todo` | `complete_todos_of_type` | "Both complete todos..." |

### Solution: Merge into single tools that handle both cases:
```python
# Instead of add_bullet_to_work() AND add_bullets_to_work():
add_bullets(work_id, bullets: Bullet | list[Bullet])  # Handles 1 or many

# Instead of add_skill() AND add_skills():
add_skills(skills: Skill | list[Skill])  # Handles 1 or many

# Instead of get_application() AND get_application_resume():
get_application(id, include_resume=True)  # One tool, optional detail

# Instead of validate_experience() AND validate_work_position():
validate(work_id: str | None = None)  # None = validate all
```

---

## Pain Point 3: Tool Names Don't Describe Outcomes

### Names that confuse agents:

| Current Name | What It Actually Does | Better Name |
|--------------|----------------------|-------------|
| `render_and_compile` | Creates a PDF file | `compile_pdf` |
| `get_experience_for_tailoring` | Returns all experience data | `get_experience` |
| `preview_tailored_resume` | Validates resume structure | `validate_resume` |
| `add_major_project_to_work` | Adds context for generating bullets | `add_work_context` |
| `complete_todos_of_type` | Bulk complete pending actions | `complete_todos` |
| `setup_storage` | Initialize directories | `initialize` |
| `check_setup_status` | Get setup state | `get_status` |

### Naming convention: `{verb}_{noun}` where noun is the OUTPUT
- ✅ `compile_pdf` - creates a pdf
- ✅ `add_bullets` - adds bullets  
- ❌ `render_and_compile` - what's the output?
- ❌ `get_experience_for_tailoring` - too verbose, implicit context

---

## Pain Point 4: No Clear Workflow Stages

### Current organization (by data type):
```
Work tools (8) → Education tools (5) → Skills tools (6) → Projects tools (6) → 
Templates (9) → Applications (13) → Workflow (7) → Search (2) → Setup (10)
```

**Problem:** Agent doesn't know what workflow stage it's in. Tools for different stages are mixed together.

### Agent-friendly organization (by workflow stage):

```
STAGE 1: SETUP (run once)
├── initialize()         - Create directories and files
├── set_basics()         - Set contact info
└── get_status()         - Check system state

STAGE 2: BUILD EXPERIENCE (ongoing, as user provides info)
├── add_work()           - Add a job position
├── add_bullets()        - Add accomplishments to a position
├── add_work_context()   - Add major project context
├── add_skills()         - Add skill categories
├── add_projects()       - Add portfolio projects
└── add_education()      - Add education entry

STAGE 3: GENERATE RESUME (per job application)
├── create_application() - Start new application (returns experience data)
├── save_and_compile()   - Save resume + generate PDF
└── generate_cover_letter() - Create cover letter

STAGE 4: MANAGE (as needed, on demand)
├── get_*()              - Read specific data
├── update_*()           - Modify existing data
├── delete_*()           - Remove data
└── search()             - Find across data
```

---

## Pain Point 5: Missing Convenience Patterns

### Things agents frequently need but don't have tools for:

**1. "Just make me a resume for this job"**
- Currently: 4 tool calls minimum
- Should be: 2 tool calls (create + save_and_compile)

**2. "Add this bullet to my most recent job"**
- Currently: Agent must call get_all_work, find most recent, then add_bullet with ID
- Should be: `add_bullets(bullet, work_id="latest")` - special convenience ID

**3. "Update just the summary for this work position"**
- Currently: get_work_by_id, modify summary, update_work (full object replacement)
- Could be: `update_work(work_id, summary="...")` - partial update support

**4. "What tools can I use with this application?"**
- Currently: Agent must know all application-related tools exist
- Should be: Tool descriptions include "Related: X, Y, Z" or return values include next steps

---

## Pain Point 6: Error Recovery is Unclear

### Current error message:
```
"✗ ERROR: Work position with ID xyz not found."
```

### Agent-friendly error message:
```
"✗ ERROR: Work position 'xyz' not found.

RECOVERY OPTIONS:
1. Use get_all_work() to list available positions and their IDs
2. Use add_work() to create a new position
3. Similar IDs found: 'xyz-123', 'abc-xyz' (did you mean one of these?)
"
```

**Implementation:** Every "not found" error should include:
- The recovery tool name
- Alternative suggestions if available
- Clear next steps

---

## Recommended Tool Structure (Agent-Optimized)

### Tier 1: Core Workflow (12 tools) - ALWAYS ENABLED
These handle 90% of use cases. Agent should always have access.

```python
# Setup (run once)
initialize()            # Create directories + experience.json
set_basics(basics)      # Set/update contact info
get_status()            # Check setup, get stats

# Experience building (ongoing)
add_work(work)                      # Add a job position
add_bullets(work_id, bullets)       # Add accomplishments (1 or many)
add_skills(skills)                  # Add skill categories (1 or many)

# Resume generation (the main workflow)
create_application(company, position, jd)  # Returns app_id + experience data
save_and_compile(app_id, resume, compile=True)  # Validate + save + PDF

# Reading data
get_experience()        # Get all experience data
get_applications()      # List all applications
get_application(id)     # Get application details + resume
```

### Tier 2: Additional Content (6 tools) - ENABLED ON DEMAND
For adding more detail beyond core workflow.

```python
add_education(education)           # Add education entry
add_projects(projects)             # Add portfolio projects
add_work_context(work_id, project) # Add major project context
update_work(work)                  # Modify existing position
update_skill(skill)                # Modify skill category
generate_cover_letter(app_id)      # Create cover letter
```

### Tier 3: Management (8 tools) - POWER USERS
For updates, deletes, and advanced operations.

```python
get_work(id)              # Single position details
delete_work(id)           # Remove position
delete_education(id)      # Remove education
delete_skill(id)          # Remove skill category
delete_application(id)    # Remove application
search(query)             # Search across all data
validate()                # Check data quality
restore_backup(index)     # Restore from backup
```

### Tier 4: Templates (4 tools) - ADVANCED
Most users use default template. These are for customization.

```python
get_templates()                           # List available
get_template(name)                        # Read template content
save_template(name, content)              # Create or update
preview_template(name, sample_data=True)  # Test template
```

### Total: 30 tools (down from 71)

---

## Migration Mapping

| Old Tools | New Tool | Notes |
|-----------|----------|-------|
| `setup_storage` + `initialize_experience` | `initialize()` | Combined setup |
| `check_setup_status` + `get_experience_stats` | `get_status()` | Combined status |
| `get_experience_for_tailoring` | *(returned by create_application)* | Eliminated |
| `save_tailored_resume` + `render_and_compile` | `save_and_compile()` | Combined |
| `preview_tailored_resume` | *(validation in save_and_compile)* | Eliminated |
| `add_bullet_to_work` + `add_bullets_to_work` | `add_bullets()` | Merged |
| `add_skill` + `add_skills` | `add_skills()` | Merged |
| `add_project` + `add_projects` | `add_projects()` | Merged |
| `get_application` + `get_application_resume` | `get_application()` | Merged |
| `validate_experience` + `validate_work_position` | `validate()` | Merged |
| `complete_todo` + `complete_todos_of_type` | `complete_todos()` | Merged |
| `list_applications` | `get_applications()` | Renamed |
| `list_templates` | `get_templates()` | Renamed |
| `add_major_project_to_work` | `add_work_context()` | Renamed |
| `generate_cover_letter_data` + `save_cover_letter` | `generate_cover_letter()` | Merged |
| `compare_resumes` | *(removed)* | Rarely used |
| `get_pending_todos_for_work` | *(filter param on get_todos)* | Consolidated |
| `clear_completed_todos` | *(auto-cleanup)* | Eliminated |
| `add_custom_todo` | *(removed)* | Rarely used |
| `filter_work_by_tags` | *(merged into search)* | Consolidated |

---

## Tool Description Template

Each tool description should follow this format for maximum agent clarity:

```python
@tool(
    name="add_bullets",
    description="""Add accomplishment bullets to a work position.

WHEN TO USE: After adding a work position, use this to add specific 
accomplishments that will appear on tailored resumes.

ACCEPTS: Single bullet or list of bullets. Work position ID required.

EXAMPLE:
  add_bullets(work_id="abc123", bullets=[
    {"text": "Led team of 5 engineers...", "tags": ["leadership"]},
    {"text": "Reduced costs by 40%...", "tags": ["cost-savings"]}
  ])

IF ERROR "position not found":
  → Use get_all_work() to list positions and find correct ID

NEXT STEPS after success:
  → Add more bullets with add_bullets()
  → Add project context with add_work_context()
  → When ready, use create_application() to generate a resume
"""
)
```

---

## Implementation Priority

### Priority 1: Applications Group (Biggest Agent Impact)
This is the workflow agents hit most often. 

**Changes:**
1. `create_application` returns experience data (eliminates get_experience_for_tailoring)
2. `save_and_compile` replaces save + render (1 tool instead of 2)
3. `get_application` includes resume by default (eliminates get_application_resume)

**Impact:** Reduces application workflow from 4 calls to 2 calls.

### Priority 2: Eliminate Ambiguous Pairs
Merge all `add_X` + `add_Xs` pairs into single tools.

**Changes:**
- `add_bullets` (accepts 1 or array)
- `add_skills` (accepts 1 or array)
- `add_projects` (accepts 1 or array)

**Impact:** Agent never has to choose between singular/plural tools.

### Priority 3: Improve Tool Descriptions
Add "WHEN TO USE", "IF ERROR", and "NEXT STEPS" to all tool descriptions.

**Impact:** Agent self-recovers from errors, knows workflow sequence.

### Priority 4: Rename for Clarity
Apply consistent `verb_noun` naming where noun is the output.

**Impact:** Agent can predict what tool does from name alone.

---

## Success Metrics

After consolidation, measure:

1. **Tool calls per workflow** - Should drop from 4+ to 2 for resume generation
2. **Error recovery rate** - Agents should self-recover more often
3. **Correct tool selection** - No more "should I use add_bullet or add_bullets?" confusion
4. **Activation issues** - With 30 tools instead of 71, less likely to be disabled

---

## Next Steps

1. ✅ Complete this analysis
2. ⬜ Implement consolidated Application tools first (biggest impact)
3. ⬜ Merge singular/plural pairs (add_bullet/add_bullets, etc.)
4. ⬜ Update all tool descriptions with agent-friendly format
5. ⬜ Test with agent workflows to validate improvements
6. ⬜ Remove deprecated tools after validation period
