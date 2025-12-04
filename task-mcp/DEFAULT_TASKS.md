# Default Border Crossing Report Tasks

The task-mcp database is **automatically populated** with Border Crossing Report tasks when a new database is created. This happens automatically when the container starts for the first time or when the database volume is recreated.

## Tasks Created

### Completed Tasks (3)

1. **September 2024 Border Crossing Report** (Task ID: 8)
   - Status: DONE
   - Priority: 5
   - Created: 2024-09-01
   - Completed: 2024-10-05
   - Metadata:
     ```json
     {
       "month": "2024-09",
       "report_type": "border_crossing",
       "completed_by": "system"
     }
     ```

2. **October 2024 Border Crossing Report** (Task ID: 9)
   - Status: DONE
   - Priority: 5
   - Created: 2024-10-01
   - Completed: 2024-11-05
   - Metadata:
     ```json
     {
       "month": "2024-10",
       "report_type": "border_crossing",
       "completed_by": "system"
     }
     ```

3. **November 2024 Border Crossing Report** (Task ID: 10)
   - Status: DONE
   - Priority: 5
   - Created: 2024-11-01
   - Completed: 2024-12-03
   - Metadata:
     ```json
     {
       "month": "2024-11",
       "report_type": "border_crossing",
       "completed_by": "system"
     }
     ```

### Pending Task (1)

4. **December 2024 Border Crossing Report** (Task ID: 11)
   - Status: PENDING
   - Priority: 10 (higher priority for current month)
   - Created: 2024-12-01
   - Due Date: 2025-01-05
   - Metadata:
     ```json
     {
       "month": "2024-12",
       "report_type": "border_crossing",
       "due_date": "2025-01-05"
     }
     ```

## Project Organization

All Border Crossing Report tasks are grouped under the project: **`monthly-reports`**

## Accessing These Tasks

### List all monthly report tasks:
```python
task_list(project_id="monthly-reports", order_by_priority=True)
```

### List only pending tasks:
```python
task_list(status="pending", project_id="monthly-reports")
```

### List completed tasks:
```python
task_list(status="done", project_id="monthly-reports")
```

### Get the December task:
```python
task_get(task_id=11)
```

### Get next pending task (will return December task):
```python
task_pop_next(project_id="monthly-reports")
```
Note: This will mark the task as "in_progress"

## How It Works

When the TaskStore class initializes, it:
1. Checks if the `tasks` table exists in the database
2. If the table doesn't exist (new database), it creates the schema
3. Automatically populates the database with the 4 default Border Crossing Report tasks

This logic is in `task_mcp/database.py` in the `_migrate()` and `_populate_default_tasks()` methods.

## Re-populating the Database

If you need to reset and re-populate the database with fresh default tasks:

```bash
# Stop the container
docker compose down task-mcp

# Remove the volume to clear the database
docker volume rm mcp-lab_task-data

# Restart the container (tasks will be auto-created)
docker compose up -d task-mcp
```

The default tasks will be automatically created when the container starts.

## Integration with Document Attachments

These tasks are ready to have documents attached. For example, to attach a completed report:

```python
# Attach the November report document
task_attach_document(
    task_id=10,  # November task
    document_id="doc_nov_2024_border_report",
    filename="Border_Crossing_Report_November_2024.pdf",
    description="Final border crossing report for November 2024"
)
```

## Workflow Example

When working on the December report:

1. Get the pending task:
   ```python
   task = task_pop_next(project_id="monthly-reports")
   # Returns task ID 11 and marks it as "in_progress"
   ```

2. Work on generating the report...

3. Attach the completed report document:
   ```python
   task_attach_document(
       task_id=11,
       document_id="doc_dec_2024_border_report",
       filename="Border_Crossing_Report_December_2024.pdf",
       description="Final border crossing report for December 2024"
   )
   ```

4. Mark the task as complete:
   ```python
   task_update(
       task_id=11,
       status="done",
       metadata={
           "month": "2024-12",
           "report_type": "border_crossing",
           "completed_by": "agent",
           "completion_date": "2024-12-20"
       }
   )
   ```

5. Create next month's task:
   ```python
   task_create(
       title="Create January 2025 Border Crossing Report",
       description="Generate monthly border crossing report for January 2025...",
       priority=10,
       metadata={"month": "2025-01", "report_type": "border_crossing"},
       project_id="monthly-reports"
   )
   ```
