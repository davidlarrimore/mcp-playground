# Task-MCP Changelog

## 2024-12-04 - Major Updates

### Document Attachments Feature

Added comprehensive document attachment support to link documents to tasks.

**Database Changes:**
- New `task_attachments` table with foreign key to tasks
- Cascade delete: attachments removed when parent task deleted
- Indexed lookups for performance

**New MCP Tools:**
- `task_attach_document` - Attach a document to a task
- `task_list_attachments` - List all attachments for a task
- `task_get_attachment` - Get attachment details
- `task_remove_attachment` - Remove an attachment

**Files Modified:**
- `task_mcp/database.py` - Added attachment methods
- `task_mcp/server.py` - Added 4 new MCP tools
- `README.md` - Updated with attachment documentation
- New file: `ATTACHMENTS_GUIDE.md` - Comprehensive attachment guide

### Automatic Default Task Population

Database now automatically populates with sample Border Crossing Report tasks on first run.

**Implementation:**
- Detection of new database (checks for existing tasks table)
- Automatic creation of 4 default tasks:
  - 3 completed tasks (September, October, November 2024)
  - 1 pending task (December 2024)
- All tasks in `monthly-reports` project
- Detailed metadata including month, report type, due dates

**Files Modified:**
- `task_mcp/database.py` - Added `_populate_default_tasks()` method
- `README.md` - Documented default task behavior
- New file: `DEFAULT_TASKS.md` - Guide to default tasks
- New file: `populate_default_tasks.py` - Manual population script (backup)

### Benefits

1. **Immediate Value**: Service ready to demonstrate with real data
2. **Testing**: No need to manually create test data
3. **Documentation**: Clear examples of task structure and workflow
4. **Integration**: Tasks ready for document attachments
5. **Repeatable**: Fresh data on every container rebuild

### Technical Details

**Database Detection:**
```python
cursor = self.conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
)
is_new_database = cursor.fetchone() is None
```

**Logging:**
- All default task creation logged at INFO level
- Clear messages showing task IDs and status
- Visible in container logs for verification

**Idempotency:**
- Only runs on new databases
- Existing databases unchanged
- Safe for upgrades

### Migration Notes

- Existing installations: No changes to data
- Fresh installations: Get default tasks automatically
- To reset: Remove volume and restart container

### Files Added

- `ATTACHMENTS_GUIDE.md` - Complete attachment documentation
- `DEFAULT_TASKS.md` - Default task reference
- `CHANGELOG.md` - This file
- `populate_default_tasks.py` - Manual population script
- `verify_tasks.py` - Task verification script
- `simple_query.py` - Simple database query script
- `test_attachments.py` - Attachment functionality tests

### Testing Performed

1. ✓ Document attachment CRUD operations
2. ✓ Automatic task population on fresh database
3. ✓ Container rebuild with volume removal
4. ✓ Log verification of task creation
5. ✓ MCP tool validation
6. ✓ Database query verification

### Backward Compatibility

- All existing MCP tools unchanged
- Database migration is additive only
- No breaking changes to API
- Existing tasks unaffected

## Future Enhancements

Potential additions discussed:
- Attachment metadata (file size, MIME type, checksum)
- Attachment versioning
- Bulk attachment operations
- Search attachments by filename
- Dynamic default task generation based on current date
