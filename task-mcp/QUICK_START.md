# Task MCP Quick Start Guide

This guide will help you quickly get started with the Task Management MCP service.

## Starting the Service

### Start with docker-compose
```bash
# From the mcp-lab root directory
docker-compose up -d task-mcp

# Check health
curl http://localhost:2007/healthz
# Should return: ok
```

### View logs
```bash
docker-compose logs -f task-mcp
```

## Testing the Service

### Option 1: Via MCPO OpenAPI UI
1. Open http://localhost:2010/task/docs in your browser
2. Use the interactive Swagger UI to test endpoints

### Option 2: Direct MCP Endpoint
The MCP endpoint is at `http://localhost:2007/mcp` (Streamable HTTP)

### Option 3: Command Line Tests

Create a task:
```bash
curl -X POST http://localhost:2010/task/task_create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement authentication",
    "description": "Add JWT-based authentication",
    "priority": 10,
    "metadata": {"tags": ["security", "backend"]},
    "project_id": "api-v2"
  }'
```

List all tasks:
```bash
curl -X POST http://localhost:2010/task/task_list \
  -H "Content-Type: application/json" \
  -d '{}'
```

List pending tasks (ordered by priority):
```bash
curl -X POST http://localhost:2010/task/task_list \
  -H "Content-Type: application/json" \
  -d '{
    "status": "pending",
    "order_by_priority": true,
    "limit": 10
  }'
```

Get a specific task:
```bash
curl -X POST http://localhost:2010/task/task_get \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'
```

Update task status:
```bash
curl -X POST http://localhost:2010/task/task_update \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "status": "in_progress"
  }'
```

Pop next task (for worker agents):
```bash
curl -X POST http://localhost:2010/task/task_pop_next \
  -H "Content-Type: application/json" \
  -d '{}'
```

Get statistics:
```bash
curl -X POST http://localhost:2010/task/task_stats \
  -H "Content-Type: application/json" \
  -d '{}'
```

Delete a task:
```bash
curl -X POST http://localhost:2010/task/task_delete \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1}'
```

## Integration with Open WebUI

### Step 1: Ensure Network Connection
If Open WebUI runs in Docker, connect it to the mcp-net network:
```bash
docker network connect mcp-net <your-openwebui-container-name>
```

### Step 2: Add MCP Server in Open WebUI

#### Option A: Via MCPO (Recommended - All Services)
1. Go to Settings → Tools → External Tools
2. Click "Add Tool Server"
3. Fill in:
   - **Type**: MCP (Streamable HTTP)
   - **URL**: `http://mcpo:8000/mcp` (or `http://host.docker.internal:2010/mcp` if not on mcp-net)
   - **Name**: `mcp-services`
4. Click "Test Connection" - should show all tools including task_*
5. Click "Save"

#### Option B: Task Service Only
1. Go to Settings → Tools → External Tools
2. Click "Add Tool Server"
3. Fill in:
   - **Type**: MCP (Streamable HTTP)
   - **URL**: `http://task-mcp:8000/mcp` (or `http://host.docker.internal:2007/mcp` if not on mcp-net)
   - **Name**: `task`
4. Click "Test Connection" - should show 7 task tools
5. Click "Save"

### Step 3: Use in Conversations

Example conversation with Open WebUI:

**You**: Create a task to implement user authentication with priority 10

**AI**: *Calls task_create tool*
Task created successfully! ID: 1

**You**: List all pending tasks ordered by priority

**AI**: *Calls task_list tool*
Here are your pending tasks:
1. Implement user authentication (priority 10)
...

**You**: Update task 1 to in progress

**AI**: *Calls task_update tool*
Task 1 has been updated to in_progress status.

## Use Cases

### 1. Project Sprint Planning
```python
# Create sprint backlog
task_create({
  "title": "Design database schema",
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
```

### 2. AI Agent Task Queue
```python
# Agent picks up highest priority task
task = task_pop_next()  # Automatically marks as in_progress

# Agent completes work...

# Mark as done
task_update({
  "task_id": task["id"],
  "status": "done",
  "metadata": {"completed_by": "agent-007", "actual_hours": 6}
})
```

### 3. Bug Tracking
```python
task_create({
  "title": "Fix login timeout issue",
  "description": "Users report timeout after 5 minutes",
  "priority": 25,
  "metadata": {
    "type": "bug",
    "severity": "high",
    "reported_by": "user@example.com",
    "github_issue": "https://github.com/org/repo/issues/123"
  }
})
```

### 4. Feature Requests
```python
task_create({
  "title": "Add dark mode toggle",
  "description": "Users want dark mode option in settings",
  "priority": 5,
  "metadata": {
    "type": "feature",
    "votes": 42,
    "requested_by": ["user1", "user2", "user3"]
  }
})
```

## Database Persistence

Tasks are stored in SQLite at `/data/tasks.db` inside the container, mounted to Docker volume `task-data`.

View tasks directly:
```bash
docker-compose exec task-mcp sqlite3 /data/tasks.db "SELECT * FROM tasks;"
```

Reset database (deletes all tasks):
```bash
docker-compose down
docker volume rm mcp-lab_task-data
docker-compose up -d task-mcp
```

Backup database:
```bash
docker-compose exec task-mcp sqlite3 /data/tasks.db ".backup /data/backup.db"
docker cp task-mcp:/data/backup.db ./task-backup-$(date +%Y%m%d).db
```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs task-mcp

# Rebuild image
docker-compose build task-mcp
docker-compose up -d task-mcp
```

### Database locked errors
SQLite uses file-level locking. This usually happens with multiple concurrent writes:
- The service uses `check_same_thread=False` to handle concurrency
- For high-traffic scenarios, consider connection pooling or upgrading to PostgreSQL

### Cannot connect from Open WebUI
Ensure network connectivity:
```bash
# If Open WebUI is in Docker
docker network connect mcp-net <openwebui-container>

# Test connectivity from inside Open WebUI container
docker exec <openwebui-container> curl http://task-mcp:8000/healthz
```

### Tasks not persisting
Check volume mount:
```bash
docker volume inspect mcp-lab_task-data
docker-compose exec task-mcp ls -la /data/
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Explore the [example use cases](README.md#usage-examples)
- Check the [main project README](../README.md) for system architecture
- View the OpenAPI documentation at http://localhost:2010/task/docs

## Getting Help

- Check logs: `docker-compose logs task-mcp`
- View all services: `docker-compose ps`
- Test health: `curl http://localhost:2007/healthz`
- Interactive docs: http://localhost:2010/task/docs
