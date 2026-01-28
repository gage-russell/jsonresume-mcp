"""Pydantic models for JSON Resume schema with MCP extensions."""

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# MCP Extension Models (our additions to JSON Resume)
# ============================================================================


class MCPBullet(BaseModel):
    """A tagged accomplishment. AI uses these to generate work.highlights for specific job applications."""

    id: str = Field(..., description="Unique identifier for this bullet")
    text: str = Field(..., description="The accomplishment text")
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for matching to job descriptions (skills, domains, achievements)",
    )


class MCPMajorProject(BaseModel):
    """Rich project context that AI uses to understand accomplishments deeply and generate compelling, tailored bullets.

    These are NOT displayed directly on resumes. Instead, the agent uses this
    rich context to generate customized bullet points that match job descriptions.
    """

    id: str = Field(..., description="Unique identifier for this project")
    name: str = Field(..., description="Project name")
    summary: str = Field(..., description="What the project was and your specific role")
    technologies: list[str] = Field(
        default_factory=list, description="Technologies, tools, and frameworks used"
    )
    challenges: str | None = Field(
        None, description="Problems faced and how you solved them"
    )
    outcomes: str | None = Field(None, description="Results, metrics, and measurable impact")
    team_context: str | None = Field(
        None, description="Team size, your role, collaboration style"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for job matching")


class MCPWorkDetails(BaseModel):
    """MCP data store for a work position. Contains all accomplishments and context.
    
    AI generates work.highlights from this when tailoring resumes for specific jobs.
    """

    id: str = Field(..., description="Unique identifier for this position")
    bullets: list[MCPBullet] = Field(
        default_factory=list,
        description="All accomplishments at this position with tags. AI filters and selects from these to populate work.highlights.",
    )
    major_projects: list[MCPMajorProject] = Field(
        default_factory=list,
        description="Rich context about major projects. Helps AI understand the depth and generate compelling bullets.",
    )
    tags: list[str] = Field(
        default_factory=list, description="Position-level tags (skills, industries, role types)"
    )


class MCPSkillDetails(BaseModel):
    """MCP metadata for a skill entry.
    
    Note: Use the standard Skill.name field for the category (e.g., 'Languages', 'Frameworks').
    Use Skill.keywords for the actual skills in that category.
    """

    id: str = Field(..., description="Unique identifier for this skill")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering/matching")


class MCPProjectDetails(BaseModel):
    """MCP metadata for a project entry."""

    id: str = Field(..., description="Unique identifier for this project")
    one_liner: str | None = Field(None, description="Brief one-line description for resume")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering/matching")


class MCPEducationDetails(BaseModel):
    """MCP metadata for an education entry."""

    id: str = Field(..., description="Unique identifier for this education entry")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering/matching")


# ============================================================================
# JSON Resume Base Models (with MCP extensions)
# ============================================================================


class Location(BaseModel):
    """Location information from JSON Resume basics section."""

    address: str | None = Field(
        None,
        description="To add multiple address lines, use \\n. For example, 1234 Glücklichkeit Straße\\nHinterhaus 5. Etage li.",
    )
    postal_code: str | None = Field(None, description="Postal code")
    city: str | None = Field(None, description="City")
    country_code: str | None = Field(
        None, description="code as per ISO-3166-1 ALPHA-2, e.g. US, AU, IN"
    )
    region: str | None = Field(
        None,
        description="The general region where you live. Can be a US state, or a province, for instance.",
    )


class Profile(BaseModel):
    """Social media profile from JSON Resume."""

    network: str | None = Field(None, description="e.g. Facebook or Twitter")
    username: str | None = Field(None, description="e.g. neutralthoughts")
    url: str | None = Field(
        None, description="e.g. http://twitter.example.com/neutralthoughts"
    )


class Basics(BaseModel):
    """Basics section from JSON Resume (header/contact info)."""

    name: str | None = Field(None, description="Full name")
    label: str | None = Field(None, description="e.g. Web Developer")
    image: str | None = Field(
        None, description="URL (as per RFC 3986) to a image in JPEG or PNG format"
    )
    email: str | None = Field(None, description="e.g. thomas@gmail.com")
    phone: str | None = Field(
        None,
        description="Phone numbers are stored as strings so use any format you like, e.g. 712-117-2923",
    )
    url: str | None = Field(
        None, description="URL (as per RFC 3986) to your website, e.g. personal homepage"
    )
    summary: str | None = Field(
        None, description="Write a short 2-3 sentence biography about yourself"
    )
    location: Location | None = Field(None, description="Location information")
    profiles: list[Profile] = Field(
        default_factory=list,
        description="Specify any number of social networks that you participate in",
    )


class Work(BaseModel):
    """Work experience entry from JSON Resume with MCP extensions."""

    name: str | None = Field(None, description="e.g. Facebook")
    position: str | None = Field(None, description="e.g. Software Engineer")
    location: str | None = Field(None, description="e.g. Menlo Park, CA")
    description: str | None = Field(None, description="e.g. Social Media Company")
    url: str | None = Field(None, description="e.g. http://facebook.example.com")
    start_date: str | None = Field(None, description="Start date (ISO 8601 format)")
    end_date: str | None = Field(None, description="End date (ISO 8601 format)")
    summary: str | None = Field(
        None, description="Give an overview of your responsibilities at the company"
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="Specify multiple accomplishments - AI generates these from mcp_details when tailoring",
    )
    # MCP Extension
    mcp_details: MCPWorkDetails | None = Field(
        None,
        description="Comprehensive accomplishment data. AI generates work.highlights from this when tailoring resumes.",
        alias="mcp-details",
    )

    model_config = ConfigDict(populate_by_name=True)


class Education(BaseModel):
    """Education entry from JSON Resume."""

    institution: str | None = Field(
        None, description="e.g. Massachusetts Institute of Technology"
    )
    url: str | None = Field(None, description="e.g. http://facebook.example.com")
    area: str | None = Field(None, description="e.g. Arts")
    study_type: str | None = Field(None, description="e.g. Bachelor")
    start_date: str | None = Field(None, description="Start date (ISO 8601 format)")
    end_date: str | None = Field(None, description="End date (ISO 8601 format)")
    score: str | None = Field(None, description="grade point average, e.g. 3.67/4.0")
    courses: list[str] = Field(
        default_factory=list, description="List notable courses/subjects"
    )
    # MCP Extension
    mcp_details: MCPEducationDetails | None = Field(
        None,
        description="MCP metadata for education management",
        alias="mcp-details",
    )

    model_config = ConfigDict(populate_by_name=True)


class Skill(BaseModel):
    """Skill entry from JSON Resume with MCP extensions."""

    name: str | None = Field(None, description="e.g. Web Development")
    level: str | None = Field(None, description="e.g. Master")
    keywords: list[str] = Field(
        default_factory=list, description="List some keywords pertaining to this skill"
    )
    # MCP Extension
    mcp_details: MCPSkillDetails | None = Field(
        None,
        description="MCP metadata for organizing and filtering skills",
        alias="mcp-details",
    )

    model_config = ConfigDict(populate_by_name=True)


class Project(BaseModel):
    """Project entry from JSON Resume with MCP extensions."""

    name: str | None = Field(None, description="e.g. The World Wide Web")
    description: str | None = Field(
        None, description="Short summary of project. e.g. Collated works of 2017."
    )
    highlights: list[str] = Field(
        default_factory=list, description="Specify multiple features"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Specify special elements involved"
    )
    start_date: str | None = Field(None, description="Start date (ISO 8601 format)")
    end_date: str | None = Field(None, description="End date (ISO 8601 format)")
    url: str | None = Field(None, description="Project URL")
    roles: list[str] = Field(
        default_factory=list,
        description="Specify your role on this project or in company",
    )
    entity: str | None = Field(
        None,
        description="Specify the relevant company/entity affiliations e.g. 'greenpeace', 'corporationXYZ'",
    )
    type: str | None = Field(
        None,
        description="e.g. 'volunteering', 'presentation', 'talk', 'application', 'conference'",
    )
    # MCP Extension
    mcp_details: MCPProjectDetails | None = Field(
        None,
        description="MCP metadata for project selection and display",
        alias="mcp-details",
    )

    model_config = ConfigDict(populate_by_name=True)


class Award(BaseModel):
    """Award entry from JSON Resume."""

    title: str | None = Field(
        None, description="e.g. One of the 100 greatest minds of the century"
    )
    date: str | None = Field(None, description="Award date (ISO 8601 format)")
    awarder: str | None = Field(None, description="e.g. Time Magazine")
    summary: str | None = Field(
        None, description="e.g. Received for my work with Quantum Physics"
    )


class Certificate(BaseModel):
    """Certificate entry from JSON Resume."""

    name: str | None = Field(None, description="e.g. Certified Kubernetes Administrator")
    date: str | None = Field(None, description="Certificate date (ISO 8601 format)")
    url: str | None = Field(None, description="e.g. http://example.com")
    issuer: str | None = Field(None, description="e.g. CNCF")


class Publication(BaseModel):
    """Publication entry from JSON Resume."""

    name: str | None = Field(None, description="e.g. The World Wide Web")
    publisher: str | None = Field(None, description="e.g. IEEE, Computer Magazine")
    release_date: str | None = Field(None, description="Release date (ISO 8601 format)")
    url: str | None = Field(None, description="Publication URL")
    summary: str | None = Field(
        None,
        description="Short summary of publication. e.g. Discussion of the World Wide Web, HTTP, HTML.",
    )


class Language(BaseModel):
    """Language entry from JSON Resume."""

    language: str | None = Field(None, description="e.g. English, Spanish")
    fluency: str | None = Field(None, description="e.g. Fluent, Beginner")


class Interest(BaseModel):
    """Interest entry from JSON Resume."""

    name: str | None = Field(None, description="e.g. Philosophy")
    keywords: list[str] = Field(
        default_factory=list, description="e.g. Friedrich Nietzsche"
    )


class Reference(BaseModel):
    """Reference entry from JSON Resume."""

    name: str | None = Field(None, description="e.g. Timothy Cook")
    reference: str | None = Field(
        None,
        description="e.g. Joe blogs was a great employee, who turned up to work at least once a week. He exceeded my expectations when it came to doing nothing.",
    )


class Volunteer(BaseModel):
    """Volunteer work entry from JSON Resume."""

    organization: str | None = Field(None, description="e.g. Facebook")
    position: str | None = Field(None, description="e.g. Software Engineer")
    url: str | None = Field(None, description="e.g. http://facebook.example.com")
    start_date: str | None = Field(None, description="Start date (ISO 8601 format)")
    end_date: str | None = Field(None, description="End date (ISO 8601 format)")
    summary: str | None = Field(
        None, description="Give an overview of your responsibilities at the company"
    )
    highlights: list[str] = Field(
        default_factory=list, description="Specify accomplishments and achievements"
    )


class Meta(BaseModel):
    """Meta information from JSON Resume."""

    canonical: str | None = Field(
        None, description="URL (as per RFC 3986) to latest version of this document"
    )
    version: str | None = Field(
        None, description="A version field which follows semver - e.g. v1.0.0"
    )
    last_modified: str | None = Field(
        None, description="Using ISO 8601 with YYYY-MM-DDThh:mm:ss"
    )


class Resume(BaseModel):
    """Complete JSON Resume with MCP extensions."""

    schema_: str | None = Field(
        None,
        description="link to the version of the schema that can validate the resume",
        alias="$schema",
    )
    basics: Basics | None = Field(None, description="Basic/contact information")
    work: list[Work] = Field(default_factory=list, description="Work experience")
    volunteer: list[Volunteer] = Field(
        default_factory=list, description="Volunteer work"
    )
    education: list[Education] = Field(default_factory=list, description="Education")
    awards: list[Award] = Field(default_factory=list, description="Awards")
    certificates: list[Certificate] = Field(
        default_factory=list, description="Certificates"
    )
    publications: list[Publication] = Field(
        default_factory=list, description="Publications"
    )
    skills: list[Skill] = Field(default_factory=list, description="Skills")
    languages: list[Language] = Field(default_factory=list, description="Languages")
    interests: list[Interest] = Field(default_factory=list, description="Interests")
    references: list[Reference] = Field(default_factory=list, description="References")
    projects: list[Project] = Field(default_factory=list, description="Projects")
    meta: Meta | None = Field(None, description="Meta information")
    # MCP Extension
    key_highlights: list[str] = Field(
        default_factory=list,
        description="Key career highlights across all experience - typically 3-5 impressive accomplishments for top of resume",
        alias="keyHighlights",
    )

    model_config = ConfigDict(populate_by_name=True)
