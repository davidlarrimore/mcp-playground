# Task Management MCP Server

A SQLite-backed task management service exposed via Model Context Protocol (MCP). This service provides a complete task registry with CRUD operations, prioritization, project grouping, and extensible metadata.

## Features

- **Full CRUD Operations**: Create, read, update, and delete tasks
- **Task Prioritization**: Higher priority tasks can be retrieved first
- **Project Grouping**: Optional project_id for organizing tasks
- **Extensible Metadata**: Store custom JSON metadata (tags, estimates, etc.)
- **Task Queue Operations**: Pop highest-priority pending tasks for worker agents
- **Statistics**: Get counts by task status
- **Document Attachments**: Attach and manage documents linked to tasks
- **Default Tasks**: Automatically populated with sample Border Crossing Report tasks
- **Persistent Storage**: SQLite database in Docker volume
- **MCP Compatible**: Full Model Context Protocol support via FastMCP

## Architecture

### Tech Stack
- **Language**: Python 3.11
- **Database**: SQLite (zero external dependencies)
- **MCP Framework**: FastMCP 2.x
- **Transport**: Streamable HTTP via supergateway
- **Containerization**: Docker with persistent volume

### Components
- `task_mcp/database.py` - SQLite database layer with TaskStore class
- `task_mcp/server.py` - FastMCP server with MCP tools
- `Dockerfile` - Container definition
- `start-task.sh` - Entry point using supergateway

## Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|in_progress|done|cancelled
    priority INTEGER NOT NULL DEFAULT 0,     -- higher = more important
    metadata TEXT,                           -- JSON for custom fields
    project_id TEXT,                         -- optional project grouping
    created_at TEXT NOT NULL,                -- ISO timestamp
    updated_at TEXT NOT NULL                 -- ISO timestamp
);
```

### Task Attachments Table
```sql
CREATE TABLE task_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    document_id TEXT NOT NULL,               -- Reference to document (e.g., from document-mcp)
    filename TEXT,                           -- Optional display filename
    description TEXT,                        -- Optional attachment description
    attached_at TEXT NOT NULL,               -- ISO timestamp
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
);
```

**Note**: Attachments are automatically deleted when their parent task is deleted (CASCADE).

## Default Tasks

When the database is first created, it's automatically populated with 4 sample Border Crossing Report tasks:
- **3 completed tasks** for September, October, and November 2024
- **1 pending task** for December 2024 (priority 10)

All default tasks are in the `monthly-reports` project. This provides immediate data for testing and demonstration purposes.

See [DEFAULT_TASKS.md](DEFAULT_TASKS.md) for details about the default tasks and how to work with them.

## MCP Tools

### task_create
Create a new task.

**Parameters:**
- `title` (string, required) - Task title
- `description` (string, optional) - Task description
- `priority` (integer, optional) - Priority level (default: 0)
- `metadata` (object, optional) - JSON metadata for extensibility
- `project_id` (string, optional) - Project identifier

**Returns:** `{task_id, message}`

**Example:**
```json
{
  "title": "Implement user authentication",
  "description": "Add JWT-based auth with refresh tokens",
  "priority": 10,
  "metadata": {
    "tags": ["security", "backend"],
    "estimated_hours": 8,
    "assignee": "alice@example.com"
  },
  "project_id": "api-v2"
}
```

### task_get
Get a single task by ID.

**Parameters:**
- `task_id` (integer, required) - Task ID

**Returns:** `{task: {...}}` or `{error: "..."}`

**Example:**
```json
{
  "task_id": 5
}
```

### task_list
List tasks with filtering and sorting.

**Parameters:**
- `status` (string, optional) - Filter by status (pending, in_progress, done, cancelled)
- `project_id` (string, optional) - Filter by project
- `order_by_priority` (boolean, optional) - Sort by priority DESC (default: true)
- `limit` (integer, optional) - Maximum number of tasks

**Returns:** `{tasks: [...], count: N}`

**Example:**
```json
{
  "status": "pending",
  "order_by_priority": true,
  "limit": 10
}
```

### task_update
Update task fields.

**Parameters:**
- `task_id` (integer, required) - Task ID
- `title` (string, optional) - New title
- `description` (string, optional) - New description
- `status` (string, optional) - New status
- `priority` (integer, optional) - New priority
- `metadata` (object, optional) - New metadata (replaces existing)
- `project_id` (string, optional) - New project ID

**Returns:** `{success: true, message: "...", task: {...}}` or `{error: "..."}`

**Example:**
```json
{
  "task_id": 5,
  "status": "in_progress",
  "priority": 15
}
```

### task_delete
Delete a task permanently.

**Parameters:**
- `task_id` (integer, required) - Task ID

**Returns:** `{success: true, message: "..."}` or `{error: "..."}`

**Example:**
```json
{
  "task_id": 5
}
```

### task_pop_next
Get the highest-priority pending task and mark it as in_progress.

**Parameters:**
- `project_id` (string, optional) - Filter by project

**Returns:** `{task: {...}, message: "..."}` or `{task: null, message: "No pending tasks"}`

**Example:**
```json
{
  "project_id": "api-v2"
}
```

### task_stats
Get task statistics.

**Parameters:** None

**Returns:** `{stats: {total, pending, in_progress, done, cancelled}}`

**Example response:**
```json
{
  "stats": {
    "total": 42,
    "pending": 12,
    "in_progress": 5,
    "done": 23,
    "cancelled": 2
  }
}
```

### task_attach_document
Attach a document to a task.

**Parameters:**
- `task_id` (integer, required) - Task ID to attach the document to
- `document_id` (string, required) - Document identifier (e.g., from document-mcp)
- `filename` (string, optional) - Filename for display purposes
- `description` (string, optional) - Description of the attachment

**Returns:** `{attachment_id, message}` or `{error: "..."}`

**Example:**
```json
{
  "task_id": 5,
  "document_id": "doc_abc123",
  "filename": "requirements.pdf",
  "description": "Project requirements document"
}
```

### task_list_attachments
List all document attachments for a task.

**Parameters:**
- `task_id` (integer, required) - Task ID to list attachments for

**Returns:** `{attachments: [...], count: N}` or `{error: "..."}`

**Example:**
```json
{
  "task_id": 5
}
```

**Example response:**
```json
{
  "attachments": [
    {
      "id": 1,
      "task_id": 5,
      "document_id": "doc_abc123",
      "filename": "requirements.pdf",
      "description": "Project requirements document",
      "attached_at": "2024-01-15T10:30:00.123456"
    }
  ],
  "count": 1
}
```

### task_get_attachment
Get details of a specific attachment.

**Parameters:**
- `attachment_id` (integer, required) - Attachment ID to retrieve

**Returns:** `{attachment: {...}}` or `{error: "..."}`

**Example:**
```json
{
  "attachment_id": 3
}
```

### task_remove_attachment
Remove a document attachment from a task.

**Parameters:**
- `attachment_id` (integer, required) - Attachment ID to remove

**Returns:** `{success: true, message: "..."}` or `{error: "..."}`

**Example:**
```json
{
  "attachment_id": 3
}
```

## Usage Examples

### Creating a Sprint Backlog

```python
# Create tasks for a sprint
task_create({
    "title": "Design database schema",
    "description": "Design tables for user profiles and preferences",
    "priority": 20,
    "metadata": {"sprint": "sprint-24", "story_points": 5},
    "project_id": "user-profiles"
})

task_create({
    "title": "Implement API endpoints",
    "priority": 15,
    "metadata": {"sprint": "sprint-24", "story_points": 8},
    "project_id": "user-profiles"
})

task_create({
    "title": "Write integration tests",
    "priority": 10,
    "metadata": {"sprint": "sprint-24", "story_points": 3},
    "project_id": "user-profiles"
})
```

### Worker Agent Pattern

```python
# Agent picks up next task
response = task_pop_next({"project_id": "user-profiles"})
task = response["task"]

# Agent works on task...
# ...

# Mark as complete
task_update({
    "task_id": task["id"],
    "status": "done",
    "metadata": {
        **task["metadata"],
        "completed_by": "agent-007",
        "actual_hours": 6
    }
})
```

### Project Dashboard

```python
# Get all pending tasks for a project
pending = task_list({
    "status": "pending",
    "project_id": "api-v2",
    "order_by_priority": true
})

# Get statistics
stats = task_stats()

# Display summary
print(f"Pending: {len(pending['tasks'])}")
print(f"Total: {stats['stats']['total']}")
```

### Document Attachment Workflow

```python
# Create a task for reviewing a proposal
result = task_create({
    "title": "Review Q1 Project Proposal",
    "description": "Review and provide feedback on the Q1 proposal",
    "priority": 10,
    "project_id": "planning-2024"
})
task_id = result["task_id"]

# Attach related documents (assuming documents are already uploaded to document-mcp)
task_attach_document({
    "task_id": task_id,
    "document_id": "doc_proposal_q1_2024",
    "filename": "Q1_Proposal.pdf",
    "description": "Main project proposal document"
})

task_attach_document({
    "task_id": task_id,
    "document_id": "doc_budget_q1_2024",
    "filename": "Q1_Budget.xlsx",
    "description": "Budget spreadsheet with cost estimates"
})

# Later, when working on the task, list all attachments
attachments = task_list_attachments({"task_id": task_id})
print(f"Task has {attachments['count']} attachment(s):")
for att in attachments["attachments"]:
    print(f"  - {att['filename']}: {att['description']}")
    # Use document_id to retrieve actual document from document-mcp
    # document_get(att['document_id'])
```

## Configuration

### Environment Variables
- `DB_PATH` - Path to SQLite database (default: `/data/tasks.db`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

### Docker Volume
The service uses a named volume `task-data` mounted at `/data` to persist the SQLite database across container restarts.

## Integration with mcp-playground

### Docker Compose
The service is defined in the main `docker-compose.yml`:

```yaml
task-mcp:
  build:
    context: ./task-mcp
  container_name: task-mcp
  restart: unless-stopped
  networks:
    - mcp-net
  ports:
    - "${TASK_MCP_PORT:-2007}:8000"
  environment:
    DB_PATH: /data/tasks.db
    LOG_LEVEL: ${LOG_LEVEL:-INFO}
  volumes:
    - task-data:/data
```

### MCPO Integration
The service is registered in `mcpo-config.json` for unified access:

```json
{
  "task": {
    "type": "streamable-http",
    "url": "http://task-mcp:8000/mcp"
  }
}
```

### Endpoints
- **MCP Endpoint**: `http://localhost:2007/mcp` (or `http://task-mcp:8000/mcp` on `mcp-net`)
- **Health Check**: `http://localhost:2007/healthz`

## Open WebUI Setup

### Option 1: Direct Connection
Add a new MCP server in Open WebUI:
- Type: `MCP (Streamable HTTP)`
- URL: `http://task-mcp:8000/mcp` (if on `mcp-net`) or `http://host.docker.internal:2007/mcp`
- Name: `task`

### Option 2: Via MCPO (Recommended)
Add MCPO as a single MCP server to access all services including task-mcp:
- Type: `MCP (Streamable HTTP)`
- URL: `http://mcpo:8000/mcp` (if on `mcp-net`) or `http://host.docker.internal:2010/mcp`

## Development

### Local Development
Run locally without Docker (requires Python 3.11+):

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_PATH=./tasks.db
export LOG_LEVEL=DEBUG

# Run server
python -m task_mcp.server
```

### Testing the Service

```bash
# Health check
curl http://localhost:2007/healthz

# Via MCPO OpenAPI docs
open http://localhost:2010/task/docs
```

## Extensibility

The task schema is designed for future enhancements:

### Potential Future Features
- **Subtasks**: Add `parent_task_id` column for hierarchical tasks
- **Tags**: Extract tags from metadata into separate table with many-to-many relationship
- **Comments**: Add `task_comments` table with foreign key to tasks
- **History/Audit**: Add `task_history` table tracking all changes
- **Due Dates**: Add `due_date` column with timezone support
- **Assignees**: Add `assigned_to` column or separate assignments table
- **Dependencies**: Add `task_dependencies` table for task relationships
- **Recurring Tasks**: Add `recurrence_rule` column with cron-like syntax
- **Attachment Metadata**: Add file size, MIME type, checksum to attachments
- **Attachment Versioning**: Track multiple versions of the same document

### Metadata Best Practices
Use the `metadata` JSON field for custom fields without schema changes:

```json
{
  "tags": ["bug", "urgent"],
  "story_points": 5,
  "assignee": "alice@example.com",
  "github_issue": "https://github.com/org/repo/issues/123",
  "estimated_hours": 8,
  "actual_hours": 6,
  "blocked_by": [45, 67],
  "custom_fields": {
    "department": "engineering",
    "customer": "acme-corp"
  }
}
```

## Troubleshooting

### Database Locked
SQLite uses file-level locking. If you see "database is locked" errors:
- Ensure only one process accesses the database
- Check for long-running transactions
- Consider connection pooling for high concurrency

### Container Restart
The database persists in the `task-data` volume. To reset and get fresh default tasks:
```bash
docker compose down task-mcp
docker volume rm mcp-lab_task-data
docker compose up -d task-mcp
```
The default Border Crossing Report tasks will be automatically created when the container starts.

### Logs
View service logs:
```bash
docker-compose logs -f task-mcp
```

## License

Part of the mcp-playground project. See main repository for license information.
