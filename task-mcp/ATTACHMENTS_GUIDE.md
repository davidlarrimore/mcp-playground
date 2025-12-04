# Task Document Attachments Guide

## Overview

The task-mcp server now supports attaching documents to tasks. This allows you to link external documents (from the document-mcp server or other sources) to your tasks for better organization and reference.

## New MCP Tools

### 1. `task_attach_document`

Attach a document to a task.

**Parameters:**
- `task_id` (int, required): The ID of the task to attach the document to
- `document_id` (str, required): Document identifier (e.g., from document-mcp server)
- `filename` (str, optional): Filename for display purposes
- `description` (str, optional): Description of the attachment

**Example:**
```python
task_attach_document(
    task_id=5,
    document_id="doc_abc123",
    filename="requirements.pdf",
    description="Project requirements document"
)
```

**Returns:**
```json
{
  "attachment_id": 1,
  "message": "Document doc_abc123 attached to task 5"
}
```

### 2. `task_list_attachments`

List all document attachments for a task.

**Parameters:**
- `task_id` (int, required): Task ID to list attachments for

**Example:**
```python
task_list_attachments(task_id=5)
```

**Returns:**
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

### 3. `task_get_attachment`

Get details of a specific attachment.

**Parameters:**
- `attachment_id` (int, required): Attachment ID to retrieve

**Example:**
```python
task_get_attachment(attachment_id=3)
```

**Returns:**
```json
{
  "attachment": {
    "id": 3,
    "task_id": 5,
    "document_id": "doc_xyz789",
    "filename": "budget.xlsx",
    "description": "Q1 Budget",
    "attached_at": "2024-01-15T11:00:00.123456"
  }
}
```

### 4. `task_remove_attachment`

Remove a document attachment from a task.

**Parameters:**
- `attachment_id` (int, required): Attachment ID to remove

**Example:**
```python
task_remove_attachment(attachment_id=3)
```

**Returns:**
```json
{
  "success": true,
  "message": "Attachment 3 removed successfully"
}
```

## Database Schema

The attachment functionality adds a new table `task_attachments`:

```sql
CREATE TABLE task_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    document_id TEXT NOT NULL,
    filename TEXT,
    description TEXT,
    attached_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
)
```

**Key features:**
- Automatic cascade deletion: When a task is deleted, all its attachments are automatically removed
- Indexed lookups: Fast retrieval of attachments by task_id
- Timestamp tracking: Records when documents were attached

## Usage Workflow

### Typical workflow for attaching documents to tasks:

1. **Create a task:**
   ```python
   result = task_create(
       title="Review project proposal",
       description="Review the Q1 project proposal and provide feedback",
       priority=5
   )
   task_id = result["task_id"]
   ```

2. **Attach related documents:**
   ```python
   task_attach_document(
       task_id=task_id,
       document_id="doc_proposal_2024_q1",
       filename="Q1_Proposal.pdf",
       description="Q1 Project Proposal Document"
   )

   task_attach_document(
       task_id=task_id,
       document_id="doc_budget_2024_q1",
       filename="Q1_Budget.xlsx",
       description="Q1 Budget Spreadsheet"
   )
   ```

3. **List attachments when working on the task:**
   ```python
   result = task_list_attachments(task_id=task_id)
   for attachment in result["attachments"]:
       print(f"{attachment['filename']}: {attachment['description']}")
   ```

4. **Remove attachments when no longer needed:**
   ```python
   task_remove_attachment(attachment_id=2)
   ```

## Integration with document-mcp

The `document_id` parameter is designed to work seamlessly with the document-mcp server. When you upload or process a document using document-mcp, you receive a document ID that you can then attach to tasks.

**Example workflow:**
1. Upload a document via document-mcp: `document_upload(file="proposal.pdf")` → returns `doc_abc123`
2. Create a task: `task_create(title="Review proposal")` → returns task ID 5
3. Link them: `task_attach_document(task_id=5, document_id="doc_abc123", filename="proposal.pdf")`

## Error Handling

All attachment tools return error messages for common issues:

- **Task not found:** `{"error": "Task 99999 not found"}`
- **Attachment not found:** `{"error": "Attachment 99999 not found"}`
- **Database errors:** `{"error": "Error attaching document: <details>"}`

## Migration

The database schema is automatically updated when the task-mcp server starts. The migration is safe and preserves all existing task data while adding the new `task_attachments` table.

## Best Practices

1. **Use descriptive filenames and descriptions** to make it easy to identify attachments
2. **Clean up old attachments** when they're no longer relevant to avoid clutter
3. **Store the actual document content** in the document-mcp server, not in the task database
4. **Use consistent document_id formats** if integrating with multiple systems
5. **Check attachment counts** before deleting tasks with many attachments

## Future Enhancements

Potential future improvements:
- Attachment metadata (file size, MIME type, checksum)
- Attachment versioning
- Bulk attachment operations
- Search attachments by filename or description
- Attachment thumbnails or previews
