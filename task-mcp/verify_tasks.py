#!/usr/bin/env python3
"""
Script to verify the Border Crossing Report tasks in the database.
"""

import sqlite3
import json
from pathlib import Path

# Database path in the Docker volume
DB_PATH = "/data/tasks.db"

def verify_tasks():
    """Verify the Border Crossing Report tasks."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 70)
    print("BORDER CROSSING REPORT TASKS")
    print("=" * 70)

    # Get all tasks in the monthly-reports project
    cursor.execute("""
        SELECT * FROM tasks
        WHERE project_id = 'monthly-reports'
        ORDER BY created_at ASC
    """)

    tasks = cursor.fetchall()

    if not tasks:
        print("No tasks found!")
    else:
        print(f"\nFound {len(tasks)} Border Crossing Report task(s):\n")

        for task in tasks:
            print(f"Task ID: {task['id']}")
            print(f"  Title: {task['title']}")
            print(f"  Status: {task['status'].upper()}")
            print(f"  Priority: {task['priority']}")
            print(f"  Created: {task['created_at']}")
            print(f"  Updated: {task['updated_at']}")

            if task['metadata']:
                metadata = json.loads(task['metadata'])
                print(f"  Metadata: {json.dumps(metadata, indent=4)}")

            print()

    # Get statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
        FROM tasks
        WHERE project_id = 'monthly-reports'
    """)

    stats = cursor.fetchone()
    print("-" * 70)
    print(f"Summary: {stats['total']} total | {stats['done']} completed | {stats['pending']} pending")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    verify_tasks()
