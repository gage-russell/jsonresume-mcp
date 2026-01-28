import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from resumejson_mcp.lib.experience.models import Resume
from resumejson_mcp.lib.storage.models import StoragePaths


BUILT_IN_TEMPLATE_NAME = "resumejson_mcp_base_resume_template.tex.j2"
DEFAULT_TEMPLATE_NAME = "default.tex.j2"

class TemplatesStore:
    """Store for managing Jinja2 LaTeX resume templates.
    
    On initialization, copies the built-in template to the user's templates folder
    as 'default.tex.j2'. Provides methods for rendering templates with resume data.
    
    Responsibilities:
        - Template CRUD (create, read, update, delete)
        - Built-in template management (copying default template)
        - Jinja2 rendering of resume data to LaTeX
        
    Used by:
        - ApplicationStore (delegates rendering here)
        - Template MCP tools (direct template management)
    """

    def __init__(self):
        self.storage_paths = StoragePaths()
        self.storage_paths.ensure_paths()
        self._copy_default_template()
        self._init_jinja_env()

    def _init_jinja_env(self) -> None:
        """Initialize or reload the Jinja2 environment."""
        
        def escape_latex(text):
            """Escape special LaTeX characters."""
            if not isinstance(text, str):
                return text
            replacements = {
                '&': r'\&',
                '%': r'\%',
                '$': r'\$',
                '#': r'\#',
                '_': r'\_',
                '{': r'\{',
                '}': r'\}',
                '~': r'\textasciitilde{}',
                '^': r'\^{}',
                '\\': r'\textbackslash{}',
            }
            # Replace backslash first to avoid double-escaping
            text = text.replace('\\', replacements['\\'])
            for char, replacement in replacements.items():
                if char != '\\':
                    text = text.replace(char, replacement)
            return text
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.storage_paths.templates_folder)),
            block_start_string='\\BLOCK{',
            block_end_string='}',
            variable_start_string='\\VAR{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # LaTeX has its own escaping rules
        )
        
        # Add LaTeX escaping filter
        self.jinja_env.filters['escape_latex'] = escape_latex

    def _copy_default_template(self) -> None:
        """Copy the built-in default template to the templates folder as default.tex.j2."""
        # Get path to built-in template (packaged with the module)
        built_in_template_path = Path(__file__).parent / "built_in_templates" / BUILT_IN_TEMPLATE_NAME
        
        # Destination path in user's templates folder
        dest_path = self.storage_paths.templates_folder / DEFAULT_TEMPLATE_NAME
        
        # Always copy to ensure users have the latest version
        if built_in_template_path.exists():
            shutil.copy2(built_in_template_path, dest_path)
        else:
            raise FileNotFoundError(f"Built-in template not found at {built_in_template_path}")

    # ========================================================================
    # Core Operations
    # ========================================================================

    def list_templates(self) -> list[str]:
        """List all available templates in the templates folder.
        
        Returns:
            List of template filenames (without paths)
        """
        if not self.storage_paths.templates_folder.exists():
            return []
        
        return [
            f.name for f in self.storage_paths.templates_folder.glob("*.tex.j2")
        ]

    def get_template(self, template_name: str | None = None) -> Template:
        """Load a Jinja2 template by name.
        
        Args:
            template_name: Name of the template file. If None, uses default template.
            
        Returns:
            Jinja2 Template object
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        name = template_name or DEFAULT_TEMPLATE_NAME
        template_path = self.storage_paths.templates_folder / name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {name}")
        
        return self.jinja_env.get_template(name)

    def render_template(self, resume_data: Resume | dict, template_name: str | None = None) -> str:
        """Render a template with resume data.
        
        Args:
            resume_data: Resume object or dict with resume data
            template_name: Name of the template file. If None, uses default template.
            
        Returns:
            Rendered LaTeX document as string
        """
        template = self.get_template(template_name)
        
        # Convert Resume object to dict if needed
        if isinstance(resume_data, Resume):
            data = resume_data.model_dump(mode="json", exclude_none=True)
        else:
            data = resume_data
        
        return template.render(**data)

    def save_rendered_template(self, 
                              resume_data: Resume | dict, 
                              output_filename: str,
                              template_name: str | None = None) -> Path:
        """Render a template and save to the output folder.
        
        Args:
            resume_data: Resume object or dict with resume data
            output_filename: Name for the output file (e.g., 'resume.tex')
            template_name: Name of the template file. If None, uses default template.
            
        Returns:
            Path to the saved file
        """
        rendered = self.render_template(resume_data, template_name)
        output_path = self.storage_paths.output_folder / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        
        return output_path

    def create_template(self, template_name: str, content: str) -> Path:
        """Create a new template file.
        
        Args:
            template_name: Name for the new template (should end in .tex.j2)
            content: Template content (Jinja2 + LaTeX)
            
        Returns:
            Path to the created template
            
        Raises:
            ValueError: If template already exists
        """
        if not template_name.endswith(".tex.j2"):
            template_name += ".tex.j2"
        
        template_path = self.storage_paths.templates_folder / template_name
        
        if template_path.exists():
            raise ValueError(f"Template already exists: {template_name}")
        
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Reload Jinja environment to pick up new template
        self._init_jinja_env()
        
        return template_path

    def update_template(self, template_name: str, content: str) -> Path:
        """Update an existing template file.
        
        Args:
            template_name: Name of the template to update
            content: New template content
            
        Returns:
            Path to the updated template
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self.storage_paths.templates_folder / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return template_path

    def delete_template(self, template_name: str) -> bool:
        """Delete a template file.
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            True if deleted, False if didn't exist
            
        Raises:
            ValueError: If trying to delete the default template
        """
        if template_name == DEFAULT_TEMPLATE_NAME:
            raise ValueError(f"Cannot delete default template: {DEFAULT_TEMPLATE_NAME}")
        
        template_path = self.storage_paths.templates_folder / template_name
        
        if template_path.exists():
            template_path.unlink()
            return True
        return False

    def read_template_content(self, template_name: str | None = None) -> str:
        """Read the raw content of a template file.
        
        Args:
            template_name: Name of the template. If None, uses default template.
            
        Returns:
            Raw template content as string
        """
        name = template_name or DEFAULT_TEMPLATE_NAME
        template_path = self.storage_paths.templates_folder / name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {name}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()