"""Store for managing job applications."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from resumejson_mcp.lib.storage.models import StoragePaths
from resumejson_mcp.lib.experience.models import Resume
from resumejson_mcp.built_in_templates.templates_store import TemplatesStore
from .models import Application


class ApplicationStore:
    """Manages job applications and their associated files.
    
    Each application is stored in a folder under output_folder:
        output_folder/{application_id}/
        ├── job_description.txt
        ├── resume.json          (tailored, clean JSON Resume)
        ├── resume.tex           (rendered LaTeX)
        └── resume.pdf           (compiled PDF)
    
    Responsibilities:
        - Application folder CRUD (create, list, get, delete)
        - Job description storage
        - Resume.json storage (with mcp-details stripping)
        - PDF compilation via pdflatex
        
    Delegates to TemplatesStore for:
        - Template management (CRUD)
        - Jinja2 rendering
    """
    
    def __init__(self):
        """Initialize ApplicationStore."""
        self.storage_paths = StoragePaths()
        self.storage_paths.ensure_paths()
        self.templates_store = TemplatesStore()
    
    def _generate_application_id(self, company: str, position: str) -> str:
        """Generate a unique application ID from company, position, and date."""
        # Sanitize company and position for use in folder name
        def sanitize(s: str) -> str:
            s = s.lower().strip()
            s = re.sub(r'[^a-z0-9]+', '_', s)
            s = s.strip('_')
            return s[:30]  # Limit length
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{sanitize(company)}_{sanitize(position)}_{date_str}"
    
    def _get_application_folder(self, application_id: str) -> Path:
        """Get the folder path for an application."""
        return self.storage_paths.output_folder / application_id
    
    # ========================================================================
    # Application CRUD
    # ========================================================================
    
    def create_application(self, company: str, position: str, job_description: str) -> Application:
        """Create a new job application folder with job description.
        
        Args:
            company: Company name
            position: Job position/title
            job_description: The job description text
            
        Returns:
            The created Application object
        """
        app_id = self._generate_application_id(company, position)
        folder = self._get_application_folder(app_id)
        
        # Check if folder already exists (rare but possible on same day)
        counter = 1
        original_id = app_id
        while folder.exists():
            app_id = f"{original_id}_{counter}"
            folder = self._get_application_folder(app_id)
            counter += 1
        
        # Create folder
        folder.mkdir(parents=True, exist_ok=True)
        
        # Save job description
        jd_path = folder / "job_description.txt"
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(job_description)
        
        # Create and return application object
        application = Application(
            id=app_id,
            company=company,
            position=position,
            job_description=job_description,
            folder_path=folder
        )
        
        return application
    
    def get_application(self, application_id: str) -> Application | None:
        """Load an application by its ID.
        
        Args:
            application_id: The application folder name/ID
            
        Returns:
            Application object or None if not found
        """
        folder = self._get_application_folder(application_id)
        
        if not folder.exists():
            return None
        
        # Read job description
        jd_path = folder / "job_description.txt"
        if not jd_path.exists():
            return None
        
        with open(jd_path, "r", encoding="utf-8") as f:
            job_description = f.read()
        
        # Parse ID to extract company/position (best effort)
        parts = application_id.rsplit("_", 2)  # Split from right to handle dates
        if len(parts) >= 3:
            company = parts[0].replace("_", " ").title()
            position = parts[1].replace("_", " ").title()
        else:
            company = application_id
            position = "Unknown"
        
        # Get folder creation time
        created_at = datetime.fromtimestamp(folder.stat().st_ctime)
        
        return Application(
            id=application_id,
            company=company,
            position=position,
            created_at=created_at,
            job_description=job_description,
            folder_path=folder
        )
    
    def list_applications(self) -> list[Application]:
        """List all applications.
        
        Returns:
            List of Application objects
        """
        applications = []
        
        if not self.storage_paths.output_folder.exists():
            return applications
        
        for folder in self.storage_paths.output_folder.iterdir():
            if folder.is_dir() and (folder / "job_description.txt").exists():
                app = self.get_application(folder.name)
                if app:
                    applications.append(app)
        
        # Sort by creation date, newest first
        applications.sort(key=lambda a: a.created_at, reverse=True)
        return applications
    
    def delete_application(self, application_id: str) -> bool:
        """Delete an application and all its files.
        
        Args:
            application_id: The application to delete
            
        Returns:
            True if deleted, False if not found
        """
        folder = self._get_application_folder(application_id)
        
        if folder.exists():
            shutil.rmtree(folder)
            return True
        return False
    
    # ========================================================================
    # Resume Operations
    # ========================================================================
    
    def save_resume(self, application_id: str, resume_data: Resume | dict) -> Path:
        """Save the tailored resume.json to an application folder.
        
        This strips all mcp-details fields to produce a clean JSON Resume.
        
        Args:
            application_id: The application folder
            resume_data: Resume object or dict (will strip mcp-details)
            
        Returns:
            Path to the saved resume.json
        """
        folder = self._get_application_folder(application_id)
        
        if not folder.exists():
            raise FileNotFoundError(f"Application not found: {application_id}")
        
        # Convert to dict if needed
        if isinstance(resume_data, Resume):
            data = resume_data.model_dump(mode="json", exclude_none=True, by_alias=True)
        else:
            data = resume_data
        
        # Strip all mcp-details fields recursively
        data = self._strip_mcp_details(data)
        
        # Save resume.json
        resume_path = folder / "resume.json"
        with open(resume_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        return resume_path
    
    def _strip_mcp_details(self, data: dict | list) -> dict | list:
        """Recursively remove all mcp-details fields from data."""
        if isinstance(data, dict):
            return {
                k: self._strip_mcp_details(v) 
                for k, v in data.items() 
                if k not in ("mcp-details", "mcp_details")
            }
        elif isinstance(data, list):
            return [self._strip_mcp_details(item) for item in data]
        else:
            return data
    
    def load_resume(self, application_id: str) -> dict | None:
        """Load the resume.json from an application folder.
        
        Args:
            application_id: The application folder
            
        Returns:
            Resume data as dict, or None if not found
        """
        folder = self._get_application_folder(application_id)
        resume_path = folder / "resume.json"
        
        if not resume_path.exists():
            return None
        
        with open(resume_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # ========================================================================
    # Rendering Operations
    # ========================================================================
    
    def render_to_latex(self, application_id: str, template_name: str = "default.tex.j2") -> Path:
        """Render resume.json to LaTeX using a template.
        
        Delegates rendering to TemplatesStore for consistency.
        
        Args:
            application_id: The application folder
            template_name: Name of the template to use
            
        Returns:
            Path to the generated resume.tex
        """
        folder = self._get_application_folder(application_id)
        
        if not folder.exists():
            raise FileNotFoundError(f"Application not found: {application_id}")
        
        # Load resume data
        resume_data = self.load_resume(application_id)
        if resume_data is None:
            raise FileNotFoundError(f"No resume.json found for application: {application_id}")
        
        # Delegate rendering to TemplatesStore
        rendered = self.templates_store.render_template(resume_data, template_name)
        
        # Save to application folder (not output_folder root)
        tex_path = folder / "resume.tex"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        
        return tex_path
    
    def compile_to_pdf(self, application_id: str) -> tuple[bool, str, Path | None]:
        """Compile resume.tex to PDF using pdflatex.
        
        Args:
            application_id: The application folder
            
        Returns:
            Tuple of (success: bool, message: str, pdf_path: Path | None)
        """
        folder = self._get_application_folder(application_id)
        tex_path = folder / "resume.tex"
        pdf_path = folder / "resume.pdf"
        
        if not tex_path.exists():
            return False, f"No resume.tex found. Run render_to_latex first.", None
        
        try:
            # Run pdflatex twice for proper reference resolution
            for _ in range(2):
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(folder), str(tex_path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False  # Don't raise on non-zero exit; check PDF existence instead
                )
            
            if pdf_path.exists():
                # Clean up auxiliary files
                for ext in ['.aux', '.log', '.out']:
                    aux_file = folder / f"resume{ext}"
                    if aux_file.exists():
                        aux_file.unlink()
                
                return True, f"PDF compiled successfully", pdf_path
            else:
                # Extract error from log if available
                log_path = folder / "resume.log"
                error_msg = "PDF compilation failed"
                if log_path.exists():
                    with open(log_path, "r") as f:
                        log_content = f.read()
                        # Find first error line
                        for line in log_content.split('\n'):
                            if line.startswith('!'):
                                error_msg = line
                                break
                return False, error_msg, None
                
        except FileNotFoundError:
            return False, "pdflatex not found. Please install TeX Live or MiKTeX.", None
        except subprocess.TimeoutExpired:
            return False, "PDF compilation timed out after 60 seconds.", None
        except Exception as e:
            return False, f"Compilation error: {str(e)}", None
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    def get_application_status(self, application_id: str) -> dict:
        """Get the status of all files in an application.
        
        Args:
            application_id: The application folder
            
        Returns:
            Dict with status of each file
        """
        folder = self._get_application_folder(application_id)
        
        return {
            "exists": folder.exists(),
            "job_description": (folder / "job_description.txt").exists(),
            "resume_json": (folder / "resume.json").exists(),
            "resume_tex": (folder / "resume.tex").exists(),
            "resume_pdf": (folder / "resume.pdf").exists(),
            "folder_path": str(folder)
        }
