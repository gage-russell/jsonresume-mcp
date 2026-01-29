"""MCP tools for managing and rendering resume templates."""

import re
from fastmcp.tools import tool

from resumejson_mcp.templates.templates_store import TemplatesStore
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.mcp.tags import TEMPLATES_TAGS, READ, CREATE, UPDATE, DELETE, VALIDATE, EXPORT


@tool(
    name="list_templates",
    tags=TEMPLATES_TAGS | {"read"},
    description="""List all available resume templates.
    
    Returns:
        Formatted list of template names"""
)
def list_templates() -> str:
    template_store = TemplatesStore()
    templates = template_store.list_templates()
    
    if not templates:
        return "No templates found. The default template should have been copied automatically."
    
    result = "📄 AVAILABLE TEMPLATES\n" + "=" * 60 + "\n\n"
    for template in templates:
        is_default = " (default)" if template == "default.tex.j2" else ""
        result += f"  • {template}{is_default}\n"
    
    result += f"\n✓ {len(templates)} template(s) available\n"
    result += f"\n📁 Location: {template_store.storage_paths.templates_folder}\n"
    
    return result


@tool(
    name="get_template_content",
    tags=TEMPLATES_TAGS | {"read"},
    description="""Read the raw content of a template file.
    
    Args:
        template_name: Name of the template. If None, uses default template.
        
    Returns:
        Raw template content"""
)
def get_template_content(template_name: str | None = None) -> str:
    template_store = TemplatesStore()
    
    try:
        content = template_store.read_template_content(template_name)
        name = template_name or "default.tex.j2"
        
        header = f"📄 TEMPLATE: {name}\n" + "=" * 60 + "\n\n"
        return header + content
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="create_template",
    tags=TEMPLATES_TAGS | {"create"},
    description="""Create a new resume template.
    
    Args:
        template_name: Name for the new template (will add .tex.j2 if not present)
        content: Template content (Jinja2 + LaTeX)
        
    Returns:
        Success message with template path"""
)
def create_template(template_name: str, content: str) -> str:
    template_store = TemplatesStore()
    
    try:
        path = template_store.create_template(template_name, content)
        return f"✓ TEMPLATE CREATED\n\nName: {path.name}\nPath: {path}\n\nYou can now use this template with render_resume."
    except ValueError as e:
        return f"❌ ERROR: {str(e)}\n\nUse update_template to modify an existing template."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="update_template",
    tags=TEMPLATES_TAGS | {"update"},
    description="""Update an existing resume template.
    
    Args:
        template_name: Name of the template to update
        content: New template content
        
    Returns:
        Success message"""
)
def update_template(template_name: str, content: str) -> str:
    template_store = TemplatesStore()
    
    try:
        path = template_store.update_template(template_name, content)
        return f"✓ TEMPLATE UPDATED\n\nName: {path.name}\nPath: {path}"
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}\n\nUse create_template to create a new template."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="delete_template",
    tags=TEMPLATES_TAGS | {"delete"},
    description="""Delete a resume template.
    
    Args:
        template_name: Name of the template to delete
        
    Returns:
        Success or error message"""
)
def delete_template(template_name: str) -> str:
    template_store = TemplatesStore()
    
    try:
        deleted = template_store.delete_template(template_name)
        if deleted:
            return f"✓ TEMPLATE DELETED: {template_name}"
        else:
            return f"❌ Template not found: {template_name}"
    except ValueError as e:
        return f"❌ ERROR: {str(e)}"
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="render_resume",
    tags=TEMPLATES_TAGS | {"export"},
    description="""Render a resume using the current experience data and a template.
    
    This reads your experience data and renders it with the specified template,
    saving the result to the output folder.
    
    Args:
        template_name: Name of the template to use. If None, uses default template.
        output_filename: Name for the output file (default: resume.tex)
        
    Returns:
        Success message with output path"""
)
def render_resume(template_name: str | None = None, output_filename: str = "resume.tex") -> str:
    template_store = TemplatesStore()
    experience_store = ExperienceStore()
    
    try:
        # Load experience data
        resume_data = experience_store.load_experience()
        
        # Render and save
        output_path = template_store.save_rendered_template(
            resume_data, 
            output_filename, 
            template_name
        )
        
        template_used = template_name or "default.tex.j2"
        
        result = "✓ RESUME RENDERED\n" + "=" * 60 + "\n\n"
        result += f"Template: {template_used}\n"
        result += f"Output: {output_path}\n"
        result += f"\n📄 Open LaTeX file: file://{output_path}\n"
        result += f"📂 Folder: file://{output_path.parent}\n"
        result += f"\nNext steps:\n"
        result += f"  1. Compile with: pdflatex {output_path.name}\n"
        result += f"  2. Or use an online LaTeX editor (Overleaf, etc.)\n"
        
        return result
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}\n\nMake sure you have experience data and the template exists."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="preview_render",
    tags=TEMPLATES_TAGS | {"read"},
    description="""Preview what the rendered resume would look like (returns LaTeX code).
    
    This renders the template with your current experience data but returns
    the LaTeX code instead of saving to a file.
    
    Args:
        template_name: Name of the template to use. If None, uses default template.
        
    Returns:
        Rendered LaTeX code (first 2000 characters)"""
)
def preview_render(template_name: str | None = None) -> str:
    template_store = TemplatesStore()
    experience_store = ExperienceStore()
    
    try:
        # Load experience data
        resume_data = experience_store.load_experience()
        
        # Render template
        rendered = template_store.render_template(resume_data, template_name)
        
        template_used = template_name or "default.tex.j2"
        
        # Return preview (truncate if too long)
        preview = rendered[:2000]
        truncated = "\n\n... (truncated, use render_resume to save full output)" if len(rendered) > 2000 else ""
        
        result = f"📄 PREVIEW: {template_used}\n" + "=" * 60 + "\n\n"
        result += preview + truncated
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"


@tool(
    name="validate_template",
    tags=TEMPLATES_TAGS | {"validate"},
    description="""Validate a template for syntax errors and required variables.
    
    Checks:
    - Jinja2 syntax errors (blocks, variables, filters)
    - Required resume variables are used (basics, work, skills, etc.)
    - LaTeX escape filter usage
    - Common template issues
    
    Args:
        template_name: Name of the template to validate. If None, validates default.
    
    Returns:
        Validation report with any issues found"""
)
def validate_template(template_name: str | None = None) -> str:
    """Validate template syntax and required variables."""
    template_store = TemplatesStore()
    
    try:
        content = template_store.read_template_content(template_name)
    except FileNotFoundError as e:
        return f"❌ ERROR: {str(e)}"
    
    name = template_name or "default.tex.j2"
    errors = []
    warnings = []
    info = []
    
    # Check Jinja2 syntax by trying to parse
    try:
        template_store.jinja_env.from_string(content)
    except Exception as e:
        errors.append(f"Jinja2 syntax error: {str(e)}")
    
    # Check for required resume variables
    required_sections = {
        "basics": ["basics.name", "basics.email", "basics.summary"],
        "work": ["work", "position", "name", "highlights"],
        "skills": ["skills", "keywords"],
        "education": ["education", "institution"],
        "projects": ["projects"],
    }
    
    content_lower = content.lower()
    
    # Check if major sections are referenced
    for section, keywords in required_sections.items():
        section_found = False
        for keyword in keywords:
            # Look for the variable in VAR{} blocks
            if f"var{{{keyword}" in content_lower or keyword in content_lower:
                section_found = True
                break
        
        if not section_found:
            info.append(f"Section '{section}' does not appear to be used in template")
    
    # Check for escape_latex filter usage
    var_pattern = r'\\VAR\{([^}]+)\}'
    variables = re.findall(var_pattern, content)
    
    text_fields = ["name", "summary", "position", "description", "text", "highlights", "institution", "area"]
    unescaped_text_vars = []
    
    for var in variables:
        is_text_field = any(field in var.lower() for field in text_fields)
        has_escape = "escape_latex" in var
        
        if is_text_field and not has_escape:
            unescaped_text_vars.append(var)
    
    if unescaped_text_vars:
        warnings.append(f"{len(unescaped_text_vars)} text variables may need escape_latex filter:")
        for var in unescaped_text_vars[:5]:
            warnings.append(f"  - \\VAR{{{var}}}")
        if len(unescaped_text_vars) > 5:
            warnings.append(f"  ... and {len(unescaped_text_vars) - 5} more")
    
    # Check for common LaTeX issues
    if "\\documentclass" not in content:
        errors.append("Missing \\documentclass - required for LaTeX")
    
    if "\\begin{document}" not in content:
        errors.append("Missing \\begin{document}")
    
    if "\\end{document}" not in content:
        errors.append("Missing \\end{document}")
    
    # Check for Jinja2 block structures
    block_pattern = r'\\BLOCK\{([^}]+)\}'
    blocks = re.findall(block_pattern, content)
    
    for_count = sum(1 for b in blocks if b.strip().startswith("for "))
    endfor_count = sum(1 for b in blocks if b.strip() == "endfor")
    if_count = sum(1 for b in blocks if b.strip().startswith("if "))
    endif_count = sum(1 for b in blocks if b.strip() == "endif")
    
    if for_count != endfor_count:
        errors.append(f"Mismatched for/endfor blocks: {for_count} for, {endfor_count} endfor")
    
    if if_count != endif_count:
        errors.append(f"Mismatched if/endif blocks: {if_count} if, {endif_count} endif")
    
    # Build report
    result = f"🔍 TEMPLATE VALIDATION: {name}\n" + "=" * 60 + "\n\n"
    
    if not errors and not warnings:
        result += "✅ VALIDATION PASSED\n\n"
        result += "Template appears to be valid.\n"
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
        result += f"📝 INFO ({len(info)}):\n"
        for item in info:
            result += f"  • {item}\n"
        result += "\n"
    
    # Template stats
    result += "-" * 60 + "\n"
    result += "📊 TEMPLATE STATS:\n"
    result += f"  • Size: {len(content)} bytes\n"
    result += f"  • Variables: {len(variables)}\n"
    result += f"  • For loops: {for_count}\n"
    result += f"  • Conditionals: {if_count}\n"
    
    return result


def _get_sample_resume_data() -> dict:
    """Generate sample resume data for template preview."""
    return {
        "basics": {
            "name": "Jane Doe",
            "label": "Senior Software Engineer",
            "email": "jane.doe@example.com",
            "phone": "(555) 123-4567",
            "url": "https://janedoe.dev",
            "summary": "Experienced software engineer with 8+ years building scalable distributed systems. Passionate about clean code, mentoring teams, and solving complex technical challenges.",
            "location": {
                "city": "San Francisco",
                "region": "CA",
                "countryCode": "US"
            },
            "profiles": [
                {"network": "LinkedIn", "username": "janedoe", "url": "https://linkedin.com/in/janedoe"},
                {"network": "GitHub", "username": "janedoe", "url": "https://github.com/janedoe"}
            ]
        },
        "keyHighlights": [
            "Led migration of monolithic architecture to microservices, reducing deployment time by 75%",
            "Built real-time data pipeline processing 1M+ events/day with 99.9% uptime",
            "Mentored team of 5 engineers, with 3 receiving promotions within 18 months"
        ],
        "work": [
            {
                "position": "Senior Software Engineer",
                "name": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "startDate": "2021-03",
                "endDate": None,
                "summary": "Leading backend infrastructure team",
                "highlights": [
                    "Architected event-driven microservices handling 1M+ daily transactions with 99.9% uptime",
                    "Reduced infrastructure costs by 40% through optimization and auto-scaling improvements",
                    "Led migration from PostgreSQL to distributed database, improving query performance by 3x",
                    "Mentored 5 junior engineers, establishing code review standards adopted company-wide"
                ]
            },
            {
                "position": "Software Engineer",
                "name": "StartupXYZ",
                "location": "Remote",
                "startDate": "2018-06",
                "endDate": "2021-02",
                "summary": "Full-stack development for B2B SaaS platform",
                "highlights": [
                    "Built core API serving 500+ enterprise customers with sub-100ms response times",
                    "Implemented CI/CD pipeline reducing deployment frequency from weekly to multiple times daily",
                    "Developed real-time notification system processing 10K+ messages per minute"
                ]
            }
        ],
        "skills": [
            {"name": "Languages", "keywords": ["Python", "Go", "TypeScript", "SQL"]},
            {"name": "Frameworks", "keywords": ["FastAPI", "Django", "React", "Node.js"]},
            {"name": "Infrastructure", "keywords": ["AWS", "Kubernetes", "Docker", "Terraform"]},
            {"name": "Databases", "keywords": ["PostgreSQL", "Redis", "MongoDB", "Elasticsearch"]}
        ],
        "education": [
            {
                "institution": "University of California, Berkeley",
                "area": "Computer Science",
                "studyType": "Bachelor of Science",
                "startDate": "2014-08",
                "endDate": "2018-05"
            }
        ],
        "projects": [
            {
                "name": "OpenSource Data Pipeline",
                "description": "High-performance ETL framework for data engineering",
                "highlights": ["500+ GitHub stars", "Used by 20+ companies in production"],
                "keywords": ["Python", "Apache Kafka", "Apache Spark"],
                "url": "https://github.com/janedoe/data-pipeline"
            }
        ]
    }


@tool(
    name="preview_template_with_sample_data",
    tags=TEMPLATES_TAGS | {"read"},
    description="""Render a template with sample data to preview the layout.
    
    Uses realistic sample resume data to show how the template will look
    without needing your actual experience data. Great for testing new
    templates or checking layout before using with real data.
    
    Args:
        template_name: Name of the template to preview. If None, uses default.
    
    Returns:
        Rendered LaTeX preview (first 3000 characters)"""
)
def preview_template_with_sample_data(template_name: str | None = None) -> str:
    """Render template with sample data to preview layout."""
    template_store = TemplatesStore()
    
    try:
        sample_data = _get_sample_resume_data()
        
        # Create a mock Resume object from sample data
        from resumejson_mcp.lib.experience.models import Resume
        
        # Render template with sample data
        rendered = template_store.render_template_from_dict(sample_data, template_name)
        
        template_used = template_name or "default.tex.j2"
        
        # Return preview (larger chunk for sample)
        preview = rendered[:3000]
        truncated = "\n\n... (truncated)" if len(rendered) > 3000 else ""
        
        result = f"📄 TEMPLATE PREVIEW (with sample data): {template_used}\n"
        result += "=" * 60 + "\n\n"
        result += "📝 This preview uses sample resume data to show template layout.\n"
        result += "   Your actual data is not used.\n\n"
        result += "-" * 60 + "\n\n"
        result += preview + truncated
        result += f"\n\n📊 Total rendered: {len(rendered)} characters"
        
        return result
    except Exception as e:
        return f"❌ ERROR: {str(e)}"
