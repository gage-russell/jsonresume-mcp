"""Helper functions for application MCP tools.

This module contains validation and formatting logic extracted from tools.py
to improve code organization and reduce file size.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from resumejson_mcp.constants import (
    MIN_KEY_HIGHLIGHTS,
    MIN_POSITION_HIGHLIGHTS,
    MIN_POSITION_COVERAGE_PCT,
    MIN_BULLET_COVERAGE_PCT,
)

if TYPE_CHECKING:
    from resumejson_mcp.lib.experience.experience_store import ExperienceStore


@dataclass
class ValidationStats:
    """Statistics from resume validation."""
    work_positions_included: int = 0
    work_positions_available: int = 0
    total_highlights: int = 0
    positions_missing_highlights: list[str] = field(default_factory=list)
    skills_included: int = 0
    skills_available: int = 0
    projects_included: int = 0
    projects_available: int = 0
    bullets_coverage_pct: float = 0
    position_coverage: list[dict] = field(default_factory=list)
    positions_excluded: list[dict] = field(default_factory=list)
    has_key_highlights: bool = False
    key_highlights_count: int = 0


@dataclass
class ValidationResult:
    """Result from resume validation."""
    is_valid: bool
    message: str
    stats: ValidationStats


def validate_resume_content(
    resume_data: dict, 
    experience_store: "ExperienceStore",
) -> ValidationResult:
    """Validate tailored resume has sufficient content.
    
    Checks:
    - keyHighlights are present (3-5 required)
    - Work positions have highlights (minimum 3, recommended 4-5)
    - Overall coverage is at least 60%
    - At least 70% of positions are included
    
    Args:
        resume_data: The tailored resume dict
        experience_store: Store to load full experience for comparison
        
    Returns:
        ValidationResult with is_valid, message, and stats
    """
    errors: list[str] = []
    warnings: list[str] = []
    stats = ValidationStats()
    
    # Validate keyHighlights - REQUIRED
    key_highlights = resume_data.get("keyHighlights", [])
    stats.key_highlights_count = len(key_highlights)
    stats.has_key_highlights = len(key_highlights) >= MIN_KEY_HIGHLIGHTS
    
    if not key_highlights:
        errors.append(f"❌ keyHighlights is REQUIRED - add {MIN_KEY_HIGHLIGHTS}-5 top achievements that match the job description")
    elif len(key_highlights) < MIN_KEY_HIGHLIGHTS:
        warnings.append(f"⚠️  Only {len(key_highlights)} keyHighlights (recommended: {MIN_KEY_HIGHLIGHTS}-5 top achievements)")
    
    # Load full experience for comparison
    try:
        full_experience = experience_store.load_experience()
    except Exception:
        return ValidationResult(True, "", stats)  # Can't validate without experience data
    
    # Build lookup of experience positions by company+title for matching
    experience_positions = _build_experience_positions_lookup(full_experience)
    
    # Count available content
    stats.work_positions_available = len(full_experience.work)
    stats.skills_available = len(full_experience.skills)
    stats.projects_available = len(full_experience.projects)
    
    total_available_bullets = sum(p["available_bullets"] for p in experience_positions.values())
    
    # Validate work positions
    _validate_work_positions(resume_data, experience_positions, stats, errors, warnings)
    
    # Build per-position coverage stats
    _build_position_coverage(experience_positions, stats)
    
    # Calculate overall bullets coverage
    if total_available_bullets > 0:
        stats.bullets_coverage_pct = round((stats.total_highlights / total_available_bullets) * 100, 1)
    
    # Validate minimum coverage (60%)
    if stats.bullets_coverage_pct < MIN_BULLET_COVERAGE_PCT and total_available_bullets > 0:
        errors.append(f"❌ Only {stats.bullets_coverage_pct}% bullet coverage - need at least {MIN_BULLET_COVERAGE_PCT}%")
    
    # Validate skills and projects
    skills = resume_data.get("skills", [])
    stats.skills_included = len(skills)
    if not skills:
        warnings.append("⚠️  No skills section included")
    
    projects = resume_data.get("projects", [])
    stats.projects_included = len(projects)
    
    # Build result message
    message = _build_validation_message(errors, warnings)
    is_valid = len(errors) == 0
    
    return ValidationResult(is_valid, message, stats)


def _build_experience_positions_lookup(full_experience) -> dict:
    """Build a lookup dict of positions from experience data."""
    positions = {}
    for work in full_experience.work:
        key = f"{work.position}|{work.name}".lower()
        bullet_count = len(work.mcp_details.bullets) if work.mcp_details and work.mcp_details.bullets else 0
        positions[key] = {
            "position": work.position,
            "company": work.name,
            "available_bullets": bullet_count,
            "included": False,
            "highlights_used": 0,
        }
    return positions


def _validate_work_positions(
    resume_data: dict,
    experience_positions: dict,
    stats: ValidationStats,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate work positions in the resume."""
    work_entries = resume_data.get("work", [])
    stats.work_positions_included = len(work_entries)
    
    if not work_entries:
        errors.append("❌ No work positions included - resume must have at least 1 work entry")
        return
    
    # Check minimum positions included (70% of available)
    min_positions_required = max(1, int(len(experience_positions) * (MIN_POSITION_COVERAGE_PCT / 100)))
    if len(work_entries) < min_positions_required:
        errors.append(
            f"❌ Only {len(work_entries)} positions included - "
            f"need at least {min_positions_required} ({MIN_POSITION_COVERAGE_PCT}% of {len(experience_positions)} available)"
        )
    
    for work in work_entries:
        position = work.get("position", "Unknown")
        company = work.get("name", "Unknown")
        highlights = work.get("highlights", [])
        
        stats.total_highlights += len(highlights)
        
        # Try to match to experience position
        key = f"{position}|{company}".lower()
        if key in experience_positions:
            experience_positions[key]["included"] = True
            experience_positions[key]["highlights_used"] = len(highlights)
        
        # Validate highlight counts
        if not highlights:
            errors.append(f"❌ {position} at {company}: No highlights (required: 4-5)")
            stats.positions_missing_highlights.append(f"{position} at {company}")
        elif len(highlights) < MIN_POSITION_HIGHLIGHTS:
            errors.append(f"❌ {position} at {company}: Only {len(highlights)} highlights (minimum: {MIN_POSITION_HIGHLIGHTS})")
        elif len(highlights) < 4:
            warnings.append(f"⚠️  {position} at {company}: Only {len(highlights)} highlights (recommended: 4-5)")


def _build_position_coverage(experience_positions: dict, stats: ValidationStats) -> None:
    """Build per-position coverage stats."""
    for pos_data in experience_positions.values():
        if pos_data["included"]:
            coverage_pct = 0
            if pos_data["available_bullets"] > 0:
                coverage_pct = round((pos_data["highlights_used"] / pos_data["available_bullets"]) * 100)
            stats.position_coverage.append({
                "position": pos_data["position"],
                "company": pos_data["company"],
                "available": pos_data["available_bullets"],
                "used": pos_data["highlights_used"],
                "coverage_pct": coverage_pct,
            })
        else:
            stats.positions_excluded.append({
                "position": pos_data["position"],
                "company": pos_data["company"],
                "available": pos_data["available_bullets"],
            })


def _build_validation_message(errors: list[str], warnings: list[str]) -> str:
    """Build the validation result message."""
    if errors:
        message = "VALIDATION FAILED:\n" + "\n".join(errors)
        if warnings:
            message += "\n\nWARNINGS:\n" + "\n".join(warnings)
        return message
    
    if warnings:
        return "WARNINGS:\n" + "\n".join(warnings)
    
    return ""


def format_coverage_report(stats: ValidationStats) -> str:
    """Format a coverage report from validation stats."""
    lines = [
        "\n📊 CONTENT COVERAGE REPORT",
        "-" * 50,
        "",
        "📋 POSITION-LEVEL COVERAGE:",
    ]
    
    # Per-position coverage
    for pos in stats.position_coverage:
        status = "✓" if pos["coverage_pct"] >= 50 else "⚠️" if pos["coverage_pct"] > 0 else "❌"
        lines.append(f"  {status} {pos['position']} at {pos['company']}")
        lines.append(f"      {pos['used']}/{pos['available']} bullets ({pos['coverage_pct']}%)")
    
    # Excluded positions
    if stats.positions_excluded:
        lines.append("")
        lines.append("❌ POSITIONS NOT INCLUDED:")
        for pos in stats.positions_excluded:
            lines.append(f"  • {pos['position']} at {pos['company']} ({pos['available']} bullets available)")
    
    # Summary stats
    lines.extend([
        "",
        "-" * 50,
        f"Work Positions: {stats.work_positions_included} of {stats.work_positions_available} included",
        f"Total Highlights: {stats.total_highlights} bullets used",
        f"Overall Coverage: {stats.bullets_coverage_pct}% of available experience",
        f"Skills: {stats.skills_included} of {stats.skills_available} categories",
        f"Projects: {stats.projects_included} of {stats.projects_available} included",
    ])
    
    # Key Highlights status
    if stats.has_key_highlights:
        lines.append(f"Key Highlights: ✓ {stats.key_highlights_count} included")
    else:
        lines.append(f"Key Highlights: ❌ {stats.key_highlights_count} (REQUIRED: 3-5)")
    
    # Positions with 0 highlights
    if stats.positions_missing_highlights:
        lines.append("")
        lines.append("⚠️  Positions with 0 highlights (INVALID):")
        for pos in stats.positions_missing_highlights:
            lines.append(f"   • {pos}")
    
    return "\n".join(lines)
