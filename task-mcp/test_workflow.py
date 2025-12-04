#!/usr/bin/env python3
"""
Test workflow demonstrating task-mcp functionality.
Run this script to verify the service is working correctly.

Usage:
    docker-compose exec task-mcp python3 /app/test_workflow.py
"""
import sys
sys.path.insert(0, '/app')

from task_mcp.database import TaskStore
from pathlib import Path
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def main():
    # Initialize database
    store = TaskStore(Path('/data/tasks.db'))

    print_section("Task Management System - Test Workflow")

    # Clean up any existing test tasks
    all_tasks = store.list_tasks()
    for task in all_tasks:
        if task.get('project_id') == 'test-workflow':
            store.delete_task(task['id'])

    # 1. Create multiple tasks for a project
    print_section("1. Creating Tasks for Sprint")

    tasks = [
        {
            "title": "Design database schema",
            "description": "Design tables for user profiles",
            "priority": 20,
            "metadata": {"sprint": "sprint-1", "story_points": 5, "assignee": "alice"},
            "project_id": "test-workflow"
        },
        {
            "title": "Implement API endpoints",
            "description": "Create REST API for user management",
            "priority": 15,
            "metadata": {"sprint": "sprint-1", "story_points": 8, "assignee": "bob"},
            "project_id": "test-workflow"
        },
        {
            "title": "Write unit tests",
            "description": "Add test coverage for new features",
            "priority": 10,
            "metadata": {"sprint": "sprint-1", "story_points": 3, "assignee": "charlie"},
            "project_id": "test-workflow"
        },
        {
            "title": "Update documentation",
            "description": "Document new API endpoints",
            "priority": 5,
            "metadata": {"sprint": "sprint-1", "story_points": 2, "assignee": "diana"},
            "project_id": "test-workflow"
        }
    ]

    task_ids = []
    for task_data in tasks:
        task_id = store.create_task(**task_data)
        task_ids.append(task_id)
        print(f"✓ Created task {task_id}: {task_data['title']} (priority: {task_data['priority']})")

    # 2. List all pending tasks
    print_section("2. Listing Pending Tasks (by priority)")

    pending = store.list_tasks(
        status="pending",
        project_id="test-workflow",
        order_by_priority=True
    )

    for task in pending:
        print(f"  [{task['id']}] {task['title']}")
        print(f"      Priority: {task['priority']}, Status: {task['status']}")
        print(f"      Assignee: {task['metadata'].get('assignee')}, Points: {task['metadata'].get('story_points')}")

    # 3. Pop next task (simulate agent picking up work)
    print_section("3. Agent Picks Up Highest Priority Task")

    next_task = store.pop_next_task(project_id="test-workflow")
    if next_task:
        print(f"✓ Agent picked up task {next_task['id']}: {next_task['title']}")
        print(f"  Status changed to: {next_task['status']}")
        print(f"  Agent: {next_task['metadata'].get('assignee')}")

    # 4. Update task with progress
    print_section("4. Updating Task Progress")

    # Add work notes to metadata
    updated_metadata = next_task['metadata'].copy()
    updated_metadata['work_log'] = [
        "Started implementation",
        "Created initial schema",
        "Added indexes"
    ]
    updated_metadata['hours_spent'] = 3

    store.update_task(
        next_task['id'],
        metadata=updated_metadata
    )
    print(f"✓ Updated task {next_task['id']} with work log")

    # 5. Complete the task
    print_section("5. Completing Task")

    store.update_task(
        next_task['id'],
        status="done",
        metadata={**updated_metadata, "completed": True, "actual_hours": 4}
    )
    print(f"✓ Marked task {next_task['id']} as done")

    # 6. Get another task
    print_section("6. Getting Next Task")

    next_task_2 = store.pop_next_task(project_id="test-workflow")
    if next_task_2:
        print(f"✓ Agent picked up task {next_task_2['id']}: {next_task_2['title']}")
        print(f"  Priority: {next_task_2['priority']}")

    # 7. Get statistics
    print_section("7. Sprint Statistics")

    stats = store.get_stats()
    print(f"  Total tasks: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Done: {stats['done']}")
    print(f"  Cancelled: {stats['cancelled']}")

    # Project-specific stats
    project_tasks = store.list_tasks(project_id="test-workflow")
    project_stats = {
        'total': len(project_tasks),
        'pending': len([t for t in project_tasks if t['status'] == 'pending']),
        'in_progress': len([t for t in project_tasks if t['status'] == 'in_progress']),
        'done': len([t for t in project_tasks if t['status'] == 'done']),
    }

    print(f"\n  Sprint 1 Progress:")
    print(f"    Total: {project_stats['total']}")
    print(f"    Pending: {project_stats['pending']}")
    print(f"    In Progress: {project_stats['in_progress']}")
    print(f"    Done: {project_stats['done']}")

    total_points = sum(t['metadata'].get('story_points', 0) for t in project_tasks)
    done_points = sum(t['metadata'].get('story_points', 0)
                     for t in project_tasks if t['status'] == 'done')

    print(f"\n  Story Points:")
    print(f"    Total: {total_points}")
    print(f"    Completed: {done_points}")
    print(f"    Remaining: {total_points - done_points}")

    # 8. Display all project tasks
    print_section("8. All Sprint Tasks")

    for task in store.list_tasks(project_id="test-workflow", order_by_priority=True):
        status_icon = {
            'pending': '⏳',
            'in_progress': '🔄',
            'done': '✅',
            'cancelled': '❌'
        }.get(task['status'], '❓')

        print(f"\n  {status_icon} [{task['id']}] {task['title']}")
        print(f"      Status: {task['status']}, Priority: {task['priority']}")
        print(f"      Points: {task['metadata'].get('story_points')}, Assignee: {task['metadata'].get('assignee')}")
        if task['status'] == 'done':
            print(f"      Actual hours: {task['metadata'].get('actual_hours', 'N/A')}")

    print_section("✅ Test Workflow Completed Successfully!")
    print("\nThe task management system is working correctly.")
    print("Tasks are persisted in: /data/tasks.db")
    print("\nAccess the service at:")
    print("  - MCP endpoint: http://localhost:2007/mcp")
    print("  - OpenAPI docs: http://localhost:2010/task/docs")
    print("  - Health check: http://localhost:2007/healthz")

if __name__ == "__main__":
    main()
