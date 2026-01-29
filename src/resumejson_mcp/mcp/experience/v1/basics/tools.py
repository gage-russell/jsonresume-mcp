"""MCP tools for managing basics (contact info)."""

from typing import Any

from fastmcp.tools import tool

from resumejson_mcp.lib.experience.experience_store import ExperienceStore
from resumejson_mcp.lib.experience.models import Basics, Location, Profile
from resumejson_mcp.mcp.tags import BASICS_TAGS, CREATE, READ, UPDATE
from .helpers import format_basics_result


@tool(
    name="get_basics",
    tags=BASICS_TAGS | {"read"},
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
    tags=BASICS_TAGS | {"update"},
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


# Valid field names for update_basics_field
BASICS_FIELDS = {
    "name": "Full name",
    "label": "Professional title/label",
    "email": "Email address",
    "phone": "Phone number",
    "url": "Website/portfolio URL",
    "summary": "Professional summary",
    "image": "Profile image URL",
}

BASICS_NESTED_FIELDS = {
    "location": "Location (city, region, country_code)",
    "profiles": "Social profiles list",
}


@tool(
    name="update_basics_field",
    tags=BASICS_TAGS | {"update"},
    description="""Update a single field in basics without replacing everything.

This is a convenience tool for making quick updates to contact info
without needing to provide the entire Basics object.

Supported simple fields:
- name: Full name
- label: Professional title (e.g., "Senior Software Engineer")
- email: Email address
- phone: Phone number
- url: Website/portfolio URL
- summary: Professional summary (2-3 sentences)
- image: Profile image URL

Nested fields (pass dict/list):
- location: {"city": "Austin", "region": "TX", "country_code": "US"}
- profiles: [{"network": "LinkedIn", "username": "...", "url": "..."}]

Args:
    field: Field name to update
    value: New value for the field

Examples:
    update_basics_field("phone", "555-123-4567")
    update_basics_field("summary", "Senior engineer with 10+ years...")
    update_basics_field("location", {"city": "Austin", "region": "TX"})"""
)
def update_basics_field(field: str, value: Any) -> str:
    """Update a single field in basics."""
    all_fields = {**BASICS_FIELDS, **BASICS_NESTED_FIELDS}
    
    if field not in all_fields:
        valid_fields = ", ".join(all_fields.keys())
        return f"""❌ Invalid field: '{field}'

Valid fields: {valid_fields}

Use get_basics to see current values."""
    
    store = ExperienceStore()
    existing = store.get_basics()
    
    if not existing:
        return """❌ No basics found. Use set_basics first to initialize contact information.

TIP: For first-time setup, use set_basics with complete contact info."""
    
    # Handle nested fields
    if field == "location":
        if isinstance(value, dict):
            existing.location = Location(**value)
        else:
            return "❌ location must be a dict with keys: city, region, country_code, address, postal_code"
    elif field == "profiles":
        if isinstance(value, list):
            existing.profiles = [Profile(**p) if isinstance(p, dict) else p for p in value]
        else:
            return "❌ profiles must be a list of profile objects"
    else:
        # Simple field update
        setattr(existing, field, value)
    
    store.set_basics(existing)
    
    field_desc = all_fields[field]
    return f"""✓ BASICS UPDATED

Field: {field} ({field_desc})
New value: {value if len(str(value)) < 100 else str(value)[:100] + '...'}

Use get_basics to see all current contact information."""


@tool(
    name="add_profile",
    tags=BASICS_TAGS | {"create"},
    description="""Add a social profile to basics (LinkedIn, GitHub, etc.).

This is a convenience tool for adding a single profile without replacing
all existing profiles.

Args:
    network: Network name (e.g., "LinkedIn", "GitHub", "Twitter")
    username: Your username on the network
    url: Full URL to your profile

Examples:
    add_profile("LinkedIn", "janedoe", "https://linkedin.com/in/janedoe")
    add_profile("GitHub", "janedoe", "https://github.com/janedoe")"""
)
def add_profile(network: str, username: str, url: str) -> str:
    """Add a social profile to basics."""
    store = ExperienceStore()
    existing = store.get_basics()
    
    if not existing:
        return """❌ No basics found. Use set_basics first to initialize contact information."""
    
    # Check if profile for this network already exists
    for i, profile in enumerate(existing.profiles):
        if profile.network and profile.network.lower() == network.lower():
            # Update existing profile
            existing.profiles[i] = Profile(network=network, username=username, url=url)
            store.set_basics(existing)
            return f"""✓ PROFILE UPDATED

Network: {network}
Username: {username}
URL: {url}

(Replaced existing {network} profile)"""
    
    # Add new profile
    existing.profiles.append(Profile(network=network, username=username, url=url))
    store.set_basics(existing)
    
    return f"""✓ PROFILE ADDED

Network: {network}
Username: {username}
URL: {url}

Total profiles: {len(existing.profiles)}"""
