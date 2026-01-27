"""MCP tools for managing basics (contact info)."""

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Basics
from .helpers import format_basics_result


@tool(
    name="get_basics",
    description="""Get the basics (contact info) from the experience store.

Returns the current contact information including:
- Name and professional label
- Email, phone, website
- Location details
- Professional summary
- Social profiles (LinkedIn, GitHub, etc.)

Use this to see what contact information is already set.

Note: Unlike other sections, basics is a single object (not a list).
There is only one basics section per resume."""
)
def get_basics() -> str:
    """Get basics."""
    store = ExperienceStore()
    basics = store.get_basics()
    
    if not basics:
        return """No basics information found in experience store.

🎯 NEXT STEPS:
1. Ask user for their contact information:
   - Full name
   - Professional label/title (e.g., "Software Engineer")
   - Email and phone
   - Location (city, state/region)
   - LinkedIn, GitHub, or portfolio URL
   - Brief professional summary (2-3 sentences)
2. Use set_basics to add this information
"""
    
    return format_basics_result(basics, "retrieved")


@tool(
    name="set_basics",
    description="""Set or update the basics (contact info) in the experience store.

This replaces ALL basics information with the provided data.
Any omitted fields will be cleared.

Use this to:
- Initialize contact information for the first time
- Update any contact details
- Add or update professional summary
- Add or update social profiles

Args:
    basics: Complete Basics object with all contact information

CRITICAL: This is a complete replacement operation. Include ALL fields
you want to keep. Any omitted fields will be set to None/empty.

Example structure:
{
    "name": "Jane Doe",
    "label": "Senior Software Engineer",
    "email": "jane@example.com",
    "phone": "555-1234",
    "url": "https://janedoe.dev",
    "summary": "Experienced software engineer with 8+ years building scalable systems...",
    "location": {
        "city": "San Francisco",
        "region": "CA",
        "country_code": "US"
    },
    "profiles": [
        {
            "network": "LinkedIn",
            "username": "janedoe",
            "url": "https://linkedin.com/in/janedoe"
        },
        {
            "network": "GitHub",
            "username": "janedoe",
            "url": "https://github.com/janedoe"
        }
    ]
}

WORKFLOW:
1. Get current basics with get_basics (if updating)
2. Merge user's changes with existing data
3. Call this tool with complete Basics object
4. Verify the update with get_basics"""
)
def set_basics(basics: Basics) -> str:
    """Set or update basics."""
    store = ExperienceStore()
    
    # Check if basics already exists to determine action
    existing = store.get_basics()
    action = "updated" if existing else "set"
    
    store.set_basics(basics)
    
    return format_basics_result(basics, action)
