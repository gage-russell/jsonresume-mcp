"""Models for job applications."""

from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, computed_field


class Application(BaseModel):
    """Represents a job application with its associated files.
    
    An application is a folder containing:
    - job_description.txt: The original job description
    - resume.json (optional): The tailored resume data (clean JSON Resume, no mcp-details)
    - resume.tex (optional): The rendered LaTeX document
    - resume.pdf (optional): The compiled PDF
    """
    
    id: str = Field(..., description="Unique identifier / folder name")
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Position/job title")
    created_at: datetime = Field(default_factory=datetime.now, description="When application was created")
    job_description: str = Field(..., description="The job description text")
    
    # These are computed from filesystem, not stored
    folder_path: Path | None = Field(None, description="Path to application folder")
    
    @computed_field
    @property
    def has_resume(self) -> bool:
        """Check if resume.json exists."""
        if self.folder_path is None:
            return False
        return (self.folder_path / "resume.json").exists()
    
    @computed_field
    @property
    def has_latex(self) -> bool:
        """Check if resume.tex exists."""
        if self.folder_path is None:
            return False
        return (self.folder_path / "resume.tex").exists()
    
    @computed_field
    @property
    def has_pdf(self) -> bool:
        """Check if resume.pdf exists."""
        if self.folder_path is None:
            return False
        return (self.folder_path / "resume.pdf").exists()
