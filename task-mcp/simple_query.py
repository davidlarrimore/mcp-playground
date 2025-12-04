#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect("/data/tasks.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== MONTHLY-REPORTS TASKS ===\n")

cursor.execute("""
    SELECT id, title, status, priority, created_at
    FROM tasks
    WHERE project_id = 'monthly-reports'
    ORDER BY created_at ASC
""")

for row in cursor.fetchall():
    status_icon = "✓" if row['status'] == 'done' else "○"
    print(f"{status_icon} [{row['id']}] {row['title']}")
    print(f"    Status: {row['status'].upper()} | Priority: {row['priority']} | Created: {row['created_at']}")

print("\n=== SUMMARY ===")
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM tasks
    WHERE project_id = 'monthly-reports'
    GROUP BY status
""")

for row in cursor.fetchall():
    print(f"{row['status']}: {row['count']}")

conn.close()
