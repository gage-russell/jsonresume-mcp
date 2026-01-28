from pathlib import Path
from pydantic import BaseModel, Field, computed_field, model_validator
import yaml


class StoragePaths(BaseModel):
    """Model representing storage paths for the hire-me application."""
    experience_folder: Path | None = Field(
        None,
        description="Directory path where experience data (positions, education, skills, projects) is stored"
    )
    output_folder: Path | None = Field(
        None,
        description="Directory path where generated resumes will be saved"
    )

    @model_validator(mode='after')
    def set_defaults(self):
        """Load defaults from config file if not provided."""
        if self.experience_folder is None or self.output_folder is None:            
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = yaml.safe_load(f) or {}
                    if self.experience_folder is None:
                        self.experience_folder = Path(config_data.get("experience_folder", self.default_experience_path))
                    if self.output_folder is None:
                        self.output_folder = Path(config_data.get("output_folder", self.default_output_path))
            else:
                if self.experience_folder is None:
                    self.experience_folder = self.default_experience_path
                if self.output_folder is None:
                    self.output_folder = self.default_output_path
        
        return self

    @computed_field
    @property
    def config_file(self) -> Path:
        """Path to the hire-me configuration file (not changable)."""
        return Path.home() / ".hire-me" / "config.yaml"
    
    @computed_field
    @property
    def experience_file(self) -> Path:
        """Path to the experience data file (not changable)."""
        return self.experience_folder / "experience.json"
    
    @computed_field
    @property
    def templates_folder(self) -> Path:
        """Path to the resume templates directory."""
        return self.experience_folder / "templates"
    
    @property
    def default_base_path(self) -> Path:
        """Default base path for hire-me storage."""
        return Path.home() / ".hire-me"
    
    @property
    def default_experience_path(self) -> Path:
        """Default experience storage path."""
        return self.default_base_path / "experience"
    
    @property
    def default_output_path(self) -> Path:
        """Default resume output path."""
        return self.default_base_path / "output"
    
    def ensure_paths(self) -> None:
        """Create storage directories if they don't exist."""
        self.experience_folder.mkdir(parents=True, exist_ok=True)
        self.templates_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def create_and_save_to_config(self) -> None:
        """Save the current storage paths to the config file."""
        self.ensure_paths()
        config_data = {
            "experience_folder": str(self.experience_folder),
            "output_folder": str(self.output_folder)
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)
