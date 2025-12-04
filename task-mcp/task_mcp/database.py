import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("task-mcp.database")


class TaskStore:
    """SQLite-backed task storage with CRUD operations and prioritization."""

    def __init__(self, db_path: Path):
        """
        Initialize the task store with a SQLite database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()
        logger.info(f"TaskStore initialized with database at {db_path}")

    def _migrate(self):
        """Create the tasks and task_attachments tables if they don't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 0,
                metadata TEXT,
                project_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                document_id TEXT NOT NULL,
                filename TEXT,
                description TEXT,
                attached_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        """)

        # Create index for faster lookups
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_attachments_task_id
            ON task_attachments(task_id)
        """)

        self.conn.commit()
        logger.info("Database schema migrated successfully")

    def _current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        task = dict(row)
        if task.get("metadata"):
            try:
                task["metadata"] = json.loads(task["metadata"])
            except json.JSONDecodeError:
                task["metadata"] = None
        return task

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> int:
        """
        Create a new task.

        Args:
            title: Task title (required)
            description: Optional task description
            priority: Task priority (higher number = higher priority)
            metadata: Optional JSON metadata
            project_id: Optional project/group identifier

        Returns:
            ID of the newly created task
        """
        now = self._current_timestamp()
        metadata_json = json.dumps(metadata) if metadata else None

        cursor = self.conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, metadata, project_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, "pending", priority, metadata_json, project_id, now, now)
        )
        self.conn.commit()
        task_id = cursor.lastrowid
        logger.info(f"Created task {task_id}: {title}")
        return task_id

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None if not found
        """
        cursor = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    def list_tasks(
        self,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        order_by_priority: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering and ordering.

        Args:
            status: Filter by status (e.g., 'pending', 'in_progress', 'done')
            project_id: Filter by project ID
            order_by_priority: Sort by priority (descending) and creation date
            limit: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        sql = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            sql += " AND status = ?"
            params.append(status)

        if project_id:
            sql += " AND project_id = ?"
            params.append(project_id)

        if order_by_priority:
            sql += " ORDER BY priority DESC, created_at ASC"
        else:
            sql += " ORDER BY created_at DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.execute(sql, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: int, **fields) -> bool:
        """
        Update task fields.

        Args:
            task_id: Task ID
            **fields: Fields to update (title, description, status, priority, metadata, project_id)

        Returns:
            True if task was updated, False if not found
        """
        # Filter out None values and unsupported fields
        allowed_fields = {"title", "description", "status", "priority", "metadata", "project_id"}
        updates = {k: v for k, v in fields.items() if k in allowed_fields and v is not None}

        if not updates:
            return False

        # Convert metadata to JSON if present
        if "metadata" in updates:
            updates["metadata"] = json.dumps(updates["metadata"])

        parts = [f"{key} = ?" for key in updates.keys()]
        params = list(updates.values())
        params.append(self._current_timestamp())
        params.append(task_id)

        sql = f"UPDATE tasks SET {', '.join(parts)}, updated_at = ? WHERE id = ?"

        cursor = self.conn.execute(sql, params)
        self.conn.commit()

        if cursor.rowcount > 0:
            logger.info(f"Updated task {task_id}: {list(updates.keys())}")
            return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if task was deleted, False if not found
        """
        cursor = self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

        if cursor.rowcount > 0:
            logger.info(f"Deleted task {task_id}")
            return True
        return False

    def pop_next_task(self, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the highest-priority pending task and mark it as in_progress.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Task dictionary or None if no pending tasks
        """
        sql = "SELECT * FROM tasks WHERE status = 'pending'"
        params = []

        if project_id:
            sql += " AND project_id = ?"
            params.append(project_id)

        sql += " ORDER BY priority DESC, created_at ASC LIMIT 1"

        cursor = self.conn.execute(sql, params)
        row = cursor.fetchone()

        if not row:
            return None

        task = self._row_to_dict(row)
        self.update_task(task["id"], status="in_progress")
        logger.info(f"Popped task {task['id']} and marked as in_progress")

        # Return updated task
        return self.get_task(task["id"])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get task statistics.

        Returns:
            Dictionary with task counts by status
        """
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM tasks
        """)
        row = cursor.fetchone()
        return dict(row)

    def attach_document(
        self,
        task_id: int,
        document_id: str,
        filename: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Attach a document to a task.

        Args:
            task_id: Task ID
            document_id: Document identifier (e.g., from document-mcp)
            filename: Optional filename for display
            description: Optional description of the attachment

        Returns:
            ID of the newly created attachment
        """
        now = self._current_timestamp()

        cursor = self.conn.execute(
            """
            INSERT INTO task_attachments (task_id, document_id, filename, description, attached_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, document_id, filename, description, now)
        )
        self.conn.commit()
        attachment_id = cursor.lastrowid
        logger.info(f"Attached document {document_id} to task {task_id}")
        return attachment_id

    def list_attachments(self, task_id: int) -> List[Dict[str, Any]]:
        """
        List all attachments for a task.

        Args:
            task_id: Task ID

        Returns:
            List of attachment dictionaries
        """
        cursor = self.conn.execute(
            "SELECT * FROM task_attachments WHERE task_id = ? ORDER BY attached_at DESC",
            (task_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def remove_attachment(self, attachment_id: int) -> bool:
        """
        Remove an attachment from a task.

        Args:
            attachment_id: Attachment ID

        Returns:
            True if attachment was removed, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM task_attachments WHERE id = ?",
            (attachment_id,)
        )
        self.conn.commit()

        if cursor.rowcount > 0:
            logger.info(f"Removed attachment {attachment_id}")
            return True
        return False

    def get_attachment(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single attachment by ID.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment dictionary or None if not found
        """
        cursor = self.conn.execute(
            "SELECT * FROM task_attachments WHERE id = ?",
            (attachment_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def close(self):
        """Close the database connection."""
        self.conn.close()
        logger.info("Database connection closed")
