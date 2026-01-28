"""MCP tools for managing and rendering resume templates."""

from fastmcp.tools import tool

from resumejson_mcp.built_in_templates.templates_store import TemplatesStore
from resumejson_mcp.lib.experience.experience_store import ExperienceStore


@tool(
    name="list_templates",
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
