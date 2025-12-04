#!/usr/bin/env python3
"""
Test script for task document attachment functionality.
"""

import asyncio
import os
from pathlib import Path
from task_mcp.database import TaskStore
from task_mcp.server import (
    task_create,
    task_attach_document,
    task_list_attachments,
    task_get_attachment,
    task_remove_attachment,
    task_get
)


async def test_attachments():
    """Test the document attachment functionality."""

    # Use a test database
    test_db = Path("/tmp/test_tasks.db")
    if test_db.exists():
        test_db.unlink()

    # Initialize task store
    from task_mcp import server
    server.task_store = TaskStore(test_db)

    print("=" * 60)
    print("Testing Task Document Attachment Functionality")
    print("=" * 60)

    # 1. Create a test task
    print("\n1. Creating a test task...")
    result = await task_create(
        title="Review project proposal",
        description="Review the Q1 project proposal and provide feedback",
        priority=5
    )
    print(f"   Result: {result}")
    task_id = result["task_id"]

    # 2. Attach a document
    print("\n2. Attaching a document to the task...")
    result = await task_attach_document(
        task_id=task_id,
        document_id="doc_proposal_2024_q1",
        filename="Q1_Proposal.pdf",
        description="Q1 Project Proposal Document"
    )
    print(f"   Result: {result}")
    attachment_id_1 = result.get("attachment_id")

    # 3. Attach another document
    print("\n3. Attaching another document...")
    result = await task_attach_document(
        task_id=task_id,
        document_id="doc_budget_2024_q1",
        filename="Q1_Budget.xlsx",
        description="Q1 Budget Spreadsheet"
    )
    print(f"   Result: {result}")
    attachment_id_2 = result.get("attachment_id")

    # 4. List all attachments for the task
    print("\n4. Listing all attachments for the task...")
    result = await task_list_attachments(task_id=task_id)
    print(f"   Result: {result}")
    print(f"   Found {result['count']} attachment(s)")
    for att in result['attachments']:
        print(f"     - {att['filename']} (ID: {att['id']}, Doc ID: {att['document_id']})")

    # 5. Get specific attachment details
    print("\n5. Getting details for first attachment...")
    result = await task_get_attachment(attachment_id=attachment_id_1)
    print(f"   Result: {result}")

    # 6. Get the task with attachments
    print("\n6. Getting task details...")
    result = await task_get(task_id=task_id)
    print(f"   Task: {result['task']['title']}")

    # 7. Remove an attachment
    print("\n7. Removing the second attachment...")
    result = await task_remove_attachment(attachment_id=attachment_id_2)
    print(f"   Result: {result}")

    # 8. Verify attachment was removed
    print("\n8. Verifying attachment list after removal...")
    result = await task_list_attachments(task_id=task_id)
    print(f"   Result: {result}")
    print(f"   Now has {result['count']} attachment(s)")

    # 9. Test error cases
    print("\n9. Testing error cases...")

    # Try to attach to non-existent task
    result = await task_attach_document(
        task_id=99999,
        document_id="doc_test",
        filename="test.pdf"
    )
    print(f"   Attach to non-existent task: {result}")

    # Try to get non-existent attachment
    result = await task_get_attachment(attachment_id=99999)
    print(f"   Get non-existent attachment: {result}")

    # Try to remove non-existent attachment
    result = await task_remove_attachment(attachment_id=99999)
    print(f"   Remove non-existent attachment: {result}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

    # Cleanup
    server.task_store.close()
    if test_db.exists():
        test_db.unlink()


if __name__ == "__main__":
    asyncio.run(test_attachments())
