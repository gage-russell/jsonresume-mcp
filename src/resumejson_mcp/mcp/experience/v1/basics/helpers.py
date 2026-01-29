"""Helper functions for basics MCP tools."""

from resumejson_mcp.lib.experience.models import Basics


def detect_missing_info(basics: Basics) -> list[str]:
    """Identify missing or incomplete information in basics."""
    missing = []
    
    if not basics.name:
        missing.append("No name - this is your full name")
    
    if not basics.email:
        missing.append("No email address")
    
    if not basics.phone:
        missing.append("No phone number")
    
    if not basics.label:
        missing.append("No label - a brief professional title (e.g., 'Software Engineer', 'Data Scientist')")
    
    if not basics.summary:
        missing.append("No summary - a 2-3 sentence professional bio")
    
    if not basics.location:
        missing.append("No location information")
    elif not basics.location.city:
        missing.append("Location missing city")
    elif not basics.location.region:
        missing.append("Location missing region/state")
    
    if not basics.profiles:
        missing.append("No social profiles (LinkedIn, GitHub, portfolio, etc.)")
    
    return missing


def format_basics_result(basics: Basics, action: str) -> str:
    """Format basics result for display to the agent."""
    # Header
    header = f"✓ BASICS {action.upper()}\n" + "=" * 60 + "\n"
    
    # Basic info
    basic_info = f"\n👤 PERSONAL INFORMATION:\n"
    basic_info += f"Name: {basics.name or '(Not set)'}\n"
    basic_info += f"Label: {basics.label or '(Not set)'}\n"
    
    if basics.email:
        basic_info += f"Email: {basics.email}\n"
    if basics.phone:
        basic_info += f"Phone: {basics.phone}\n"
    if basics.url:
        basic_info += f"Website: {basics.url}\n"
    
    # Location section
    location_section = ""
    if basics.location:
        loc = basics.location
        location_section = f"\n📍 LOCATION:\n"
        if loc.address:
            location_section += f"Address: {loc.address}\n"
        if loc.city:
            location_section += f"City: {loc.city}\n"
        if loc.region:
            location_section += f"Region: {loc.region}\n"
        if loc.postal_code:
            location_section += f"Postal Code: {loc.postal_code}\n"
        if loc.country_code:
            location_section += f"Country: {loc.country_code}\n"
    
    # Summary section
    summary_section = ""
    if basics.summary:
        summary_section = f"\n📝 SUMMARY:\n{basics.summary}\n"
    
    # Profiles section
    profiles_section = ""
    if basics.profiles:
        profiles_section = f"\n🔗 SOCIAL PROFILES ({len(basics.profiles)}):\n"
        for profile in basics.profiles:
            network = profile.network or "Unknown"
            username = profile.username or "(No username)"
            profiles_section += f"  • {network}: {username}"
            if profile.url:
                profiles_section += f" - {profile.url}"
            profiles_section += "\n"
    
    # Missing information
    missing = detect_missing_info(basics)
    missing_section = ""
    if missing:
        missing_section = f"\n⚠️  MISSING/INCOMPLETE INFORMATION:\n"
        missing_section += "\n".join(f"  • {m}" for m in missing)
        missing_section += "\n\n⚠️  IMPORTANT: Ask targeted follow-up questions to complete this information.\n"
    
    # Next steps guidance
    next_steps = f"\n🎯 NEXT STEPS:\n"
    next_steps += f"1. Show user the captured information above\n"
    next_steps += f"2. Ask: \"Does this contact information look correct?\"\n"
    
    if missing:
        next_steps += f"3. ⚠️  CRITICAL: This basics section is missing important information.\n"
        next_steps += f"   Ask specific follow-up questions to complete it.\n"
        next_steps += f"4. Update basics once you have more information\n"
        next_steps += f"5. Move on to work experience, skills, or projects\n"
    else:
        next_steps += f"3. ✓ Contact information looks complete!\n"
        next_steps += f"4. Move on to work experience, skills, or projects\n"
    
    next_steps += f"\n💡 NOTE: The basics section contains contact info and professional summary.\n"
    next_steps += f"         This appears at the top of every resume.\n"
    
    return header + basic_info + location_section + summary_section + profiles_section + missing_section + next_steps
