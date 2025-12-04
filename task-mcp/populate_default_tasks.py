#!/usr/bin/env python3
"""
Script to populate the task-mcp database with default Border Crossing Report tasks.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Database path in the Docker volume
DB_PATH = "/data/tasks.db"

def populate_tasks():
    """Add default Border Crossing Report tasks to the database."""

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create timestamps for each month
    # September task - completed in early October
    sept_created = "2024-09-01T08:00:00.000000"
    sept_updated = "2024-10-05T14:30:00.000000"

    # October task - completed in early November
    oct_created = "2024-10-01T08:00:00.000000"
    oct_updated = "2024-11-05T15:45:00.000000"

    # November task - completed in early December
    nov_created = "2024-11-01T08:00:00.000000"
    nov_updated = "2024-12-03T16:20:00.000000"

    # December task - created at start of month, still pending
    dec_created = "2024-12-01T08:00:00.000000"
    dec_updated = "2024-12-01T08:00:00.000000"

    # Define the tasks
    tasks = [
        {
            "title": "Create September 2024 Border Crossing Report",
            "description": "Generate monthly border crossing report for September 2024 including traffic statistics, wait times, and incident summaries",
            "status": "done",
            "priority": 5,
            "metadata": '{"month": "2024-09", "report_type": "border_crossing", "completed_by": "system"}',
            "project_id": "monthly-reports",
            "created_at": sept_created,
            "updated_at": sept_updated
        },
        {
            "title": "Create October 2024 Border Crossing Report",
            "description": "Generate monthly border crossing report for October 2024 including traffic statistics, wait times, and incident summaries",
            "status": "done",
            "priority": 5,
            "metadata": '{"month": "2024-10", "report_type": "border_crossing", "completed_by": "system"}',
            "project_id": "monthly-reports",
            "created_at": oct_created,
            "updated_at": oct_updated
        },
        {
            "title": "Create November 2024 Border Crossing Report",
            "description": "Generate monthly border crossing report for November 2024 including traffic statistics, wait times, and incident summaries",
            "status": "done",
            "priority": 5,
            "metadata": '{"month": "2024-11", "report_type": "border_crossing", "completed_by": "system"}',
            "project_id": "monthly-reports",
            "created_at": nov_created,
            "updated_at": nov_updated
        },
        {
            "title": "Create December 2024 Border Crossing Report",
            "description": "Generate monthly border crossing report for December 2024 including traffic statistics, wait times, and incident summaries",
            "status": "pending",
            "priority": 10,
            "metadata": '{"month": "2024-12", "report_type": "border_crossing", "due_date": "2025-01-05"}',
            "project_id": "monthly-reports",
            "created_at": dec_created,
            "updated_at": dec_updated
        }
    ]

    # Insert tasks
    print("Populating task database with Border Crossing Report tasks...")
    for task in tasks:
        cursor.execute("""
            INSERT INTO tasks (title, description, status, priority, metadata, project_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task["title"],
            task["description"],
            task["status"],
            task["priority"],
            task["metadata"],
            task["project_id"],
            task["created_at"],
            task["updated_at"]
        ))
        task_id = cursor.lastrowid
        print(f"  ✓ Created task {task_id}: {task['title']} (status: {task['status']})")

    conn.commit()
    conn.close()

    print("\n✓ Database populated successfully!")
    print(f"  - 3 completed tasks (September, October, November)")
    print(f"  - 1 pending task (December)")

if __name__ == "__main__":
    populate_tasks()
