import logging
import os
from typing import List, Optional

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import EmailStr

from email_mcp.server import Attachment, SendEmailRequest, _send_email

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("email-mcp-server")

server = FastMCP("email-mcp")


@server.tool()
async def send_email(
    to: List[EmailStr],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    cc: Optional[List[EmailStr]] = None,
    attachments: Optional[List[dict]] = None,
) -> dict:
    """
    Send an email via SMTP with optional attachments.
    """
    payload = SendEmailRequest(
        to=to,
        cc=cc or [],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=[Attachment(**item) for item in (attachments or [])],
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
    server.run()
