"""Setup and configuration tools for resumejson-mcp storage."""

from fastmcp.prompts import prompt
from fastmcp.tools import tool
from fastmcp.resources import resource

from resumejson_mcp.lib.storage.models import StoragePaths
from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Resume


@prompt(
    name="setup_guide",
    description="Request help setting up resumejson-mcp storage and configuration"
)
def setup_storage_prompt() -> str:
    """Prompt template for user requesting setup assistance."""
    paths = StoragePaths()
    return f"""I need help setting up my resumejson-mcp experience storage system.

Please ask me where I'd like to store:
1. My experience data (work, education, skills, projects)
2. Generated resume outputs

If I don't specify custom paths, use these defaults:
- Experience data: {paths.experience_folder}
- Resume outputs: {paths.output_folder}

Once I provide the paths (or confirm defaults), please initialize the directories and save the configuration."""


@tool(
    name="setup_storage",
    description="Initialize or update resumejson-mcp storage directories and save configuration"
)
def setup_storage(storage_paths: StoragePaths) -> str:
    """Set up storage directories and save configuration to disk."""
    try:
        storage_paths.create_and_save_to_config()
        return (
            f"✓ Successfully set up experience storage at: {storage_paths.experience_folder}\n"
            f"✓ Successfully set up resume output at: {storage_paths.output_folder}\n"
            f"✓ Configuration saved to: {storage_paths.config_file}"
        )
    except Exception as e:
        return f"✗ Error setting up storage paths: {str(e)}"


@tool(
    name="initialize_experience",
    description="Initialize a new experience.json file with empty JSON Resume structure"
)
def initialize_experience() -> str:
    """Create a new experience.json file if it doesn't already exist."""
    store = ExperienceStore()
    
    if store.experience_exists():
        return f"""⚠️  Experience file already exists at: {store.experience_file_path}

Use get_all_work and other tools to view and manage existing data.
If you want to start fresh, manually delete the file first."""
    
    try:
        store.initialize_experience()
        return f"""✓ Successfully initialized experience.json at: {store.experience_file_path}

The file has been created with an empty JSON Resume structure.
You can now start adding:
- Work experience (use add_work)
- Education (coming soon)
- Skills (coming soon)
- Projects (coming soon)

NEXT STEPS:
Ask the user: "Let's start building your experience data. What work position would you like to add first?"
"""
    except Exception as e:
        return f"✗ Error initializing experience file: {str(e)}"


@tool(
    name="check_setup_status",
    description="Check if resumejson-mcp is configured and verify that all required directories exist"
)
def check_setup_status() -> str:
    """Check the current setup status and configuration."""
    paths = StoragePaths()
    store = ExperienceStore()
    
    experience_folder_exists = paths.experience_folder.exists()
    output_folder_exists = paths.output_folder.exists()
    config_exists = paths.config_file.exists()
    experience_file_exists = store.experience_file_path.exists()
    
    status = []
    status.append("resumejson-mcp Setup Status")
    status.append("=" * 60)
    status.append(f"{'✓' if config_exists else '✗'} Config file: {paths.config_file}")
    status.append(f"{'✓' if experience_folder_exists else '✗'} Experience folder: {paths.experience_folder}")
    status.append(f"{'✓' if output_folder_exists else '✗'} Output folder: {paths.output_folder}")
    status.append(f"{'✓' if experience_file_exists else '✗'} Experience file: {store.experience_file_path}")
    status.append("")
    
    if all([experience_folder_exists, output_folder_exists, config_exists, experience_file_exists]):
        status.append("✓ Setup complete! Ready to use.")
        status.append("")
        status.append("Available tools:")
        status.append("  • get_all_work - View your work experience")
        status.append("  • add_work - Add a new work position")
    elif config_exists and experience_folder_exists:
        status.append("⚠️  Storage configured but experience file missing.")
        status.append("")
        status.append("NEXT STEP:")
        status.append("Run initialize_experience() to create your experience.json file.")
    else:
        status.append("⚠️  Setup incomplete.")
        status.append("")
        status.append("NEXT STEP:")
        status.append("Run setup_storage() to configure storage paths.")
    
    return "\n".join(status)


@resource(
    uri="storage://paths",
    name="Current Storage Paths",
    description="Current configuration for experience data and resume output directories"
)
def get_storage_paths() -> str:
    """Get the current storage path configuration."""
    return StoragePaths().model_dump_json(indent=2)


@resource(uri="experience://data/experience.json")
async def get_experience_json() -> str:
    """Access the complete experience.json file containing all career data.
    
    This JSON file contains your comprehensive career experience data including:
    - Work history with bullets and major projects
    - Education background
    - Skills organized by category
    - Portfolio projects
    - Personal information (basics)
    
    Use this resource to:
    - Review the complete data structure
    - Understand what information is already captured
    - Validate the JSON Resume format with MCP extensions
    """
    store = ExperienceStore()
    if not store.experience_file_path.exists():
        return '{"error": "Experience file not found. Use initialize_experience tool first."}'
    
    return store.experience_file_path.read_text()
