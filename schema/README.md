# JSON Resume AI Extensions Schema

This directory contains the extension schema for JSON Resume that enables AI-powered resume building and tailoring.

## Overview

The extension schema adds `x-` prefixed fields to the standard JSON Resume v1.0.0 format. These extensions are:
- **Optional** - All standard JSON Resume tools work without them
- **Non-breaking** - Validators ignore unknown fields
- **AI-optimized** - Designed for intelligent resume tailoring

## Schema Files

- **`extensions.json`** - The formal JSON Schema defining all extensions
- **`examples/extended-resume.json`** - Complete example showing all extensions in use

## Extension Fields

### Work Experience Extensions (`x-` fields in `work[]`)

| Field | Type | Description |
|-------|------|-------------|
| `x-id` | string | Unique identifier for linking and references |
| `x-tags` | array[string] | Tags for job matching (skills, industries, etc.) |
| `x-projectDetails` | array[object] | Rich project context for AI tailoring |
| `x-bullets` | array[object] | Structured bullet points with metadata |

### Project Details Structure

```json
{
  "id": "string",              // Required: Unique ID
  "name": "string",            // Required: Project name
  "summary": "string",         // Required: What and your role
  "technologies": ["string"],  // Tech stack used
  "challenges": "string",      // Problems you solved
  "outcomes": "string",        // Results and metrics
  "teamContext": "string",     // Team size and dynamics
  "tags": ["string"]          // For matching
}
```

### Skills Extensions (`x-` fields in `skills[]`)

| Field | Type | Description |
|-------|------|-------------|
| `x-id` | string | Unique identifier |
| `x-category` | string | Skill category (Languages, Frameworks, etc.) |
| `x-tags` | array[string] | Additional matching tags |
| `x-yearsOfExperience` | number | Years of experience |

### Education Extensions (`x-` fields in `education[]`)

| Field | Type | Description |
|-------|------|-------------|
| `x-id` | string | Unique identifier |
| `x-tags` | array[string] | Tags for filtering |

### Projects Extensions (`x-` fields in `projects[]`)

| Field | Type | Description |
|-------|------|-------------|
| `x-id` | string | Unique identifier |
| `x-tags` | array[string] | Tags for matching |
| `x-technologies` | array[string] | Technologies used |

## Why These Extensions?

### The Problem
Standard JSON Resume captures **what** you did, but not the **context** AI needs to:
- Generate tailored bullet points
- Match experience to job descriptions
- Select relevant projects per role
- Understand impact and scope

### The Solution
Extensions provide rich context that:
- **Humans never see directly** - Used by AI to generate tailored content
- **Enable intelligent matching** - Tags link experience to job requirements
- **Preserve details** - Full project context for any tailoring scenario
- **Stay organized** - IDs and structure for programmatic access

## Usage with AI Agents

```
User: "I worked on a microservices migration at TechCorp"

AI stores in work.highlights:
- "Migrated monolith to microservices, improving performance by 40%"

AI stores in work.x-projectDetails:
{
  "name": "Microservices Migration",
  "technologies": ["Python", "AWS", "Docker"],
  "challenges": "Legacy code, zero-downtime requirement...",
  "outcomes": "40% performance improvement, zero incidents...",
  "teamContext": "Led 5 engineers..."
}

Later, user applies to backend role:
AI generates targeted resume using project details + tags
```

## Compatibility

✅ **Works with standard JSON Resume tools** - Extensions are ignored  
✅ **Validates with jsonresume/resume-schema** - Unknown fields allowed  
✅ **Export to any theme** - Standard fields render normally  
✅ **Publish to jsonresume.org** - Extensions stripped if needed

## Validation

To validate a resume with extensions:

```bash
# Validate standard fields
resume validate resume.json

# Validate extensions (requires this schema)
# Coming soon: jsonresume-mcp validate --extensions
```

## Contributing

Found a useful extension? Open an issue or PR! We're building this with the community to eventually propose to JSON Resume.

## References

- [JSON Resume Schema v1.0.0](https://github.com/jsonresume/resume-schema)
- [JSON Schema Draft 07](http://json-schema.org/draft-07/schema)
- [Extension Naming Conventions](http://json-schema.org/latest/json-schema-validation.html#rfc.section.7.1)
