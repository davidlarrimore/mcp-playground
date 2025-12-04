import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP

from .database import TaskStore

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("task-mcp")

# Database path - use a volume-mounted location for persistence
DB_PATH = Path(os.getenv("DB_PATH", "/data/tasks.db"))

# Initialize FastMCP server
mcp = FastMCP("task")

# Initialize task store
task_store = TaskStore(DB_PATH)


@mcp.tool
async def task_create(
    title: str,
    description: Optional[str] = None,
    priority: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
    project_id: Optional[str] = None
) -> dict:
    """
    Create a new task.

    Args:
        title: Task title (required)
        description: Optional task description
        priority: Task priority (higher number = higher priority, default 0)
        metadata: Optional JSON metadata for extensibility (tags, custom fields, etc.)
        project_id: Optional project/group identifier

    Returns:
        Dictionary with task_id and confirmation message

    Example:
        task_create(
            title="Implement user authentication",
            description="Add JWT-based auth with refresh tokens",
            priority=10,
            metadata={"tags": ["security", "backend"], "estimated_hours": 8},
            project_id="api-v2"
        )
    """
    try:
        task_id = task_store.create_task(
            title=title,
            description=description,
            priority=priority,
            metadata=metadata,
            project_id=project_id
        )
        return {
            "task_id": task_id,
            "message": f"Task '{title}' created successfully with ID {task_id}"
        }
    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_get(task_id: int) -> dict:
    """
    Get a single task by ID.

    Args:
        task_id: Task ID to retrieve

    Returns:
        Task dictionary with all fields or error if not found

    Example:
        task_get(task_id=5)
    """
    try:
        task = task_store.get_task(task_id)
        if task:
            return {"task": task}
        return {"error": f"Task {task_id} not found"}
    except Exception as e:
        error_msg = f"Error retrieving task: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_list(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    order_by_priority: bool = True,
    limit: Optional[int] = None
) -> dict:
    """
    List tasks with optional filtering and ordering.

    Args:
        status: Filter by status ('pending', 'in_progress', 'done', 'cancelled')
        project_id: Filter by project ID
        order_by_priority: Sort by priority (descending) and creation date (default True)
        limit: Maximum number of tasks to return

    Returns:
        Dictionary with list of tasks and count

    Example:
        task_list(status="pending", order_by_priority=True, limit=10)
    """
    try:
        tasks = task_store.list_tasks(
            status=status,
            project_id=project_id,
            order_by_priority=order_by_priority,
            limit=limit
        )
        return {
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        error_msg = f"Error listing tasks: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_update(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    project_id: Optional[str] = None
) -> dict:
    """
    Update task fields. Only provided fields will be updated.

    Args:
        task_id: Task ID to update (required)
        title: New task title
        description: New task description
        status: New status ('pending', 'in_progress', 'done', 'cancelled')
        priority: New priority (higher number = higher priority)
        metadata: New metadata (will replace existing metadata)
        project_id: New project ID

    Returns:
        Success message or error

    Example:
        task_update(task_id=5, status="in_progress", priority=15)
    """
    try:
        fields = {}
        if title is not None:
            fields["title"] = title
        if description is not None:
            fields["description"] = description
        if status is not None:
            fields["status"] = status
        if priority is not None:
            fields["priority"] = priority
        if metadata is not None:
            fields["metadata"] = metadata
        if project_id is not None:
            fields["project_id"] = project_id

        if not fields:
            return {"error": "No fields provided to update"}

        success = task_store.update_task(task_id, **fields)
        if success:
            # Return updated task
            task = task_store.get_task(task_id)
            return {
                "success": True,
                "message": f"Task {task_id} updated successfully",
                "task": task
            }
        return {"error": f"Task {task_id} not found"}
    except Exception as e:
        error_msg = f"Error updating task: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_delete(task_id: int) -> dict:
    """
    Delete a task permanently.

    Args:
        task_id: Task ID to delete

    Returns:
        Success message or error

    Example:
        task_delete(task_id=5)
    """
    try:
        success = task_store.delete_task(task_id)
        if success:
            return {
                "success": True,
                "message": f"Task {task_id} deleted successfully"
            }
        return {"error": f"Task {task_id} not found"}
    except Exception as e:
        error_msg = f"Error deleting task: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_pop_next(project_id: Optional[str] = None) -> dict:
    """
    Get the highest-priority pending task and automatically mark it as 'in_progress'.
    Useful for workflows where agents/workers pick tasks from a queue.

    Args:
        project_id: Optional project ID to filter by

    Returns:
        Task dictionary (now marked in_progress) or null if no pending tasks

    Example:
        task_pop_next()
        task_pop_next(project_id="api-v2")
    """
    try:
        task = task_store.pop_next_task(project_id=project_id)
        if task:
            return {
                "task": task,
                "message": f"Task {task['id']} popped and marked as in_progress"
            }
        return {
            "task": None,
            "message": "No pending tasks available"
        }
    except Exception as e:
        error_msg = f"Error popping next task: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool
async def task_stats() -> dict:
    """
    Get task statistics including counts by status.

    Returns:
        Dictionary with task counts (total, pending, in_progress, done, cancelled)

    Example:
        task_stats()
    """
    try:
        stats = task_store.get_stats()
        return {"stats": stats}
    except Exception as e:
        error_msg = f"Error retrieving stats: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


if __name__ == "__main__":
    logger.info(f"Starting task-mcp server with database at {DB_PATH}")
    mcp.run()
