# resumejson-mcp

A Model Context Protocol (MCP) server for managing JSON Resume data with MCP extensions. This server provides tools for storing and managing comprehensive career experience data that can be used to generate tailored resumes.

## Features

- **JSON Resume Schema**: Standard resume format with custom MCP extensions
- **Work Experience Management**: Add, update, delete work positions with nested bullets and projects
- **Experience Resource**: Access your complete experience.json data via MCP
- **Intelligent Guidance**: Built-in prompts to help agents extract complete information

## Installation

```bash
uv sync
```

## Adding the MCP to VS Code

1. Open your VS Code settings and locate the MCP servers configuration
2. Add the following configuration:

```json
{
  "mcpServers": {
    "resumejson-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/resumejson-mcp",
        "run",
        "resumejson-mcp"
      ]
    }
  }
}
```

3. Replace `/path/to/resumejson-mcp` with the actual path to your cloned repository
4. Restart VS Code or reload the MCP servers
5. The server will be available with tools for managing work experience

## Usage

The MCP server provides the following tools:

- `get_all_work` - List all work positions
- `get_work_by_id` - Get details of a specific position
- `add_work` - Add a new work position with bullets and projects
- `update_work` - Update an existing position
- `delete_work` - Remove a position
- `add_bullet_to_work` - Add a single bullet to a position
- `add_major_project_to_work` - Add a major project to a position

### Resource

- `experience://data/experience.json` - Access the complete experience data file

## Data Structure

Experience data is stored in `~/.resumejson-mcp/experience/experience.json` following the JSON Resume schema with MCP extensions:

```json
{
  "basics": { /* name, email, phone, location, profiles */ },
  "work": [
    {
      "name": "Company Name",
      "position": "Job Title",
      "startDate": "2020-01",
      "endDate": "2023-12",
      "summary": "Role description",
      "url": "https://company.com",
      "location": "City, State",
      "mcp-details": {
        "id": "unique-id",
        "bullets": [
          { "id": "bullet-1", "text": "Accomplishment", "tags": ["skill"] }
        ],
        "major_projects": [
          {
            "id": "project-1",
            "name": "Project Name",
            "summary": "What you built and your role",
            "technologies": ["Python", "FastAPI"],
            "outcomes": "Results and metrics",
            "tags": ["backend"]
          }
        ],
        "tags": ["python", "api"]
      }
    }
  ],
  "education": [],
  "skills": [],
  "projects": []
}
```
