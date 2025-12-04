#!/usr/bin/env python3
"""
Test script to verify Border Crossing Report tasks can be accessed via MCP tools.
"""

import asyncio
from pathlib import Path
from task_mcp.database import TaskStore
from task_mcp.server import task_list, task_get, task_stats

# Use the actual database path
DB_PATH = Path("/data/tasks.db")

async def test_border_tasks():
    """Test accessing Border Crossing Report tasks via MCP tools."""

    # Initialize task store with actual database
    from task_mcp import server
    server.task_store = TaskStore(DB_PATH)

    print("=" * 70)
    print("Testing Border Crossing Report Tasks via MCP Tools")
    print("=" * 70)

    # Test 1: Get all tasks in monthly-reports project
    print("\n1. Listing all monthly-reports tasks:")
    result = await task_list(project_id="monthly-reports", order_by_priority=True)
    print(f"   Found {result['count']} task(s)")
    for task in result['tasks']:
        status_icon = "✓" if task['status'] == 'done' else "○"
        print(f"   {status_icon} [{task['id']}] {task['title']} (Status: {task['status']})")

    # Test 2: Get pending tasks only
    print("\n2. Listing pending monthly-reports tasks:")
    result = await task_list(status="pending", project_id="monthly-reports")
    print(f"   Found {result['count']} pending task(s)")
    for task in result['tasks']:
        print(f"   ○ [{task['id']}] {task['title']} (Priority: {task['priority']})")

    # Test 3: Get completed tasks
    print("\n3. Listing completed monthly-reports tasks:")
    result = await task_list(status="done", project_id="monthly-reports")
    print(f"   Found {result['count']} completed task(s)")
    for task in result['tasks']:
        print(f"   ✓ [{task['id']}] {task['title']}")

    # Test 4: Get specific task (December)
    print("\n4. Getting December 2024 task details:")
    result = await task_get(task_id=11)
    if 'task' in result:
        task = result['task']
        print(f"   Task ID: {task['id']}")
        print(f"   Title: {task['title']}")
        print(f"   Description: {task['description']}")
        print(f"   Status: {task['status']}")
        print(f"   Priority: {task['priority']}")
        print(f"   Metadata: {task['metadata']}")

    # Test 5: Get overall statistics
    print("\n5. Overall task statistics:")
    result = await task_stats()
    stats = result['stats']
    print(f"   Total: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   In Progress: {stats['in_progress']}")
    print(f"   Done: {stats['done']}")
    print(f"   Cancelled: {stats['cancelled']}")

    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)

    server.task_store.close()

if __name__ == "__main__":
    asyncio.run(test_border_tasks())
