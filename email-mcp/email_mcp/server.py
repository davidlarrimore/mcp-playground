import logging
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from pydantic import BeforeValidator
from typing_extensions import Annotated

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("email-mcp")

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_FROM_DEFAULT = os.getenv("SMTP_FROM_DEFAULT", "noreply@example.test")
ATTACH_ROOT = Path(os.getenv("ATTACH_ROOT", "/attachments")).resolve()


class Attachment(BaseModel):
    path: str = Field(..., description="Relative path under ATTACH_ROOT")
    filename: Optional[str] = Field(
        None, description="Optional filename override for the attachment"
    )


def _normalize_attachment_input(value: object) -> Attachment:
    """
    Accept Attachment, dict, or string (absolute or relative) and coerce to Attachment.
    Absolute paths must live under ATTACH_ROOT; relative paths are forced to posix form.
    """
    if isinstance(value, Attachment):
        return value
    if isinstance(value, str):
        path_obj = Path(value)
        if path_obj.is_absolute():
            try:
                cleaned = str(path_obj.resolve().relative_to(ATTACH_ROOT))
            except ValueError as exc:
                raise ValueError(
                    f"Attachment path must be under {ATTACH_ROOT}: {value}"
                ) from exc
        else:
            cleaned = path_obj.as_posix().lstrip("/")
        return Attachment(path=cleaned)
    if isinstance(value, dict):
        data = dict(value)
        if "path" in data and isinstance(data["path"], str):
            data["path"] = Path(data["path"]).as_posix().lstrip("/")
        return Attachment(**data)
    raise TypeError("attachments must be provided as strings or objects with a path")


AttachmentInput = Annotated[Attachment, BeforeValidator(_normalize_attachment_input)]


class SendEmailRequest(BaseModel):
    to: List[EmailStr]
    cc: List[EmailStr] = []
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[AttachmentInput] = Field(
        default_factory=list,
        description="Attachments as path strings or objects (path, optional filename) under ATTACH_ROOT",
    )

    def require_body(self) -> None:
        if not self.body_text and not self.body_html:
            raise ValueError("body_text or body_html must be provided")


app = FastAPI(title="Email MCP", version="0.1.0")


def _attach_files(message: EmailMessage, attachments: List[Attachment]) -> None:
    for attachment in attachments:
        source_path = (ATTACH_ROOT / attachment.path).resolve()

        if ATTACH_ROOT not in source_path.parents and source_path != ATTACH_ROOT:
            raise HTTPException(
                status_code=400,
                detail=f"Attachment path escapes ATTACH_ROOT: {attachment.path}",
            )

        if not source_path.exists() or not source_path.is_file():
            raise HTTPException(
                status_code=404, detail=f"Attachment not found: {attachment.path}"
            )

        mime_type, _ = mimetypes.guess_type(source_path.name)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        with source_path.open("rb") as fh:
            data = fh.read()
        message.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.filename or source_path.name,
        )


def _send_email(payload: SendEmailRequest) -> None:
    payload.require_body()

    message = EmailMessage()
    message["Subject"] = payload.subject
    message["From"] = SMTP_FROM_DEFAULT
    message["To"] = ", ".join(payload.to)
    if payload.cc:
        message["Cc"] = ", ".join(payload.cc)

    if payload.body_text:
        message.set_content(payload.body_text)
    if payload.body_html:
        message.add_alternative(payload.body_html, subtype="html")

    _attach_files(message, payload.attachments)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - defensive logging for ops
        logger.exception("Failed to send email via SMTP")
        raise HTTPException(
            status_code=502, detail=f"SMTP send failed: {exc}"
        ) from exc


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.post("/send")
async def send_email(request: SendEmailRequest) -> dict:
    logger.info(
        "Sending email via SMTP host=%s port=%s to=%s attachments=%s",
        SMTP_HOST,
        SMTP_PORT,
        request.to,
        [att.path for att in request.attachments],
    )
    try:
        _send_email(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "sent",
        "to": request.to,
        "cc": request.cc,
        "attachments": [att.filename or att.path for att in request.attachments],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
