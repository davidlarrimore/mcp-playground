import logging
import os
from pathlib import Path
from typing import List, Optional, Union
from typing_extensions import Annotated

from fastapi import HTTPException
from fastmcp import FastMCP
from pydantic import EmailStr

from email_mcp.server import ATTACH_ROOT, Attachment, SendEmailRequest, _send_email

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("email-mcp-server")

mcp = FastMCP("email-mcp")


def _normalize_attachment(item: object) -> Attachment:
    """
    Accept either a raw path string or a dict and return an Attachment model.
    Paths that are absolute are made relative to ATTACH_ROOT when possible.
    """

    if isinstance(item, Attachment):
        return item

    if isinstance(item, str):
        path_obj = Path(item)
        if path_obj.is_absolute():
            try:
                cleaned = str(path_obj.resolve().relative_to(ATTACH_ROOT))
            except ValueError as exc:
                raise ValueError(
                    f"Attachment path must be under {ATTACH_ROOT}: {item}"
                ) from exc
        else:
            cleaned = item.lstrip("/")
        return Attachment(path=cleaned)

    if isinstance(item, dict):
        data = dict(item)
        if "path" in data and isinstance(data["path"], str):
            path_obj = Path(data["path"])
            if path_obj.is_absolute():
                try:
                    data["path"] = str(path_obj.resolve().relative_to(ATTACH_ROOT))
                except ValueError as exc:
                    raise ValueError(
                        f"Attachment path must be under {ATTACH_ROOT}: {data['path']}"
                    ) from exc
            else:
                data["path"] = path_obj.as_posix().lstrip("/")
        return Attachment(**data)

    raise ValueError(
        "attachments must be provided as strings or dicts with at least a 'path' key"
    )


@mcp.tool
async def send_email(
    to: List[EmailStr],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    cc: Optional[List[EmailStr]] = None,
    attachments: Annotated[
        Optional[List[Union[Attachment, str, dict]]],
        "Attachments as dicts or paths under ATTACH_ROOT",
    ] = None,
) -> dict:
    """
    Send an email via SMTP with optional attachments.

    Email Body Format:
    - To send HTML emails: Use ONLY the body_html parameter with valid HTML markup (e.g., "<html><body><h1>Title</h1><p>Content</p></body></html>")
    - To send plain text emails: Use ONLY the body_text parameter
    - To send multipart emails: Provide BOTH body_text (fallback) and body_html (preferred display)
    - At least ONE of body_text or body_html MUST be provided

    IMPORTANT: When sending HTML emails, do NOT put HTML markup in body_text. Use body_html exclusively for HTML content.

    Attachments can be provided as list items of either:
    - string paths relative to ATTACH_ROOT
    - dictionaries matching the Attachment schema (path, optional filename)

    Example HTML email:
    {
        "to": ["user@example.com"],
        "subject": "HTML Email Example",
        "body_html": "<html><body><h1>Welcome</h1><p>This is an <strong>HTML</strong> email.</p></body></html>"
    }
    """
    try:
        normalized_attachments = [
            _normalize_attachment(item) for item in (attachments or [])
        ]
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    payload = SendEmailRequest(
        to=to,
        cc=cc or [],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=normalized_attachments,
    )
    try:
        _send_email(payload)
    except HTTPException as exc:
        raise ValueError(exc.detail) from exc
    return {
        "status": "sent",
        "to": payload.to,
        "cc": payload.cc,
        "attachments": [att.filename or att.path for att in payload.attachments],
    }


if __name__ == "__main__":
    mcp.run()
