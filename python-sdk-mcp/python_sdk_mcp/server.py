import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# Allow importing the shared download URL helper when mounted by Docker
sys.path.append(str(Path(__file__).resolve().parents[2]))
try:
    from shared.download_urls import generate_signed_url  # type: ignore
except Exception:  # pragma: no cover - best-effort import
    generate_signed_url = None

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("python-sdk-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))
STREAM_PATH = os.getenv("MCP_PATH", "/mcp")

mcp = FastMCP(
    name="python-sdk-demo",
    instructions=(
        "Workspace helper built with the official MCP Python SDK. "
        "List and read files from the shared workspace, or create lightweight notes with front matter."
    ),
    host=HOST,
    port=PORT,
    streamable_http_path=STREAM_PATH,
    stateless_http=True,
    json_response=True,
)


def _resolve_path(path_str: str) -> Path:
    """Resolve a workspace-relative path and guard against escaping."""
    candidate = (WORKSPACE / path_str).resolve()
    if not candidate.is_relative_to(WORKSPACE):
        raise ValueError("Path must stay within the workspace")
    return candidate


def _file_info(path: Path) -> dict:
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path.relative_to(WORKSPACE)),
        "size": stat.st_size,
        "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
    }


def _signed_url(path: Path) -> dict:
    if generate_signed_url is None:
        return {}
    try:
        info = generate_signed_url(str(path))
        return {
            "download_url": info["url"],
            "download_expires_at": info["expires_at"],
            "download_expires_in": info["expires_in"],
        }
    except Exception as exc:  # pragma: no cover - download service optional
        logger.warning("Could not generate signed URL: %s", exc)
        return {}


def _gather_files(pattern: Optional[str], recursive: bool, include_hidden: bool, limit: int) -> list[Path]:
    search = pattern or "*"
    iterator = WORKSPACE.rglob(search) if recursive else WORKSPACE.glob(search)
    files: list[Path] = []
    for path in iterator:
        if path.is_dir():
            continue
        if not include_hidden and path.name.startswith("."):
            continue
        files.append(path)
        if len(files) >= limit:
            break
    return files


@mcp.tool()
def list_workspace_files(
    pattern: Optional[str] = None,
    recursive: bool = False,
    limit: int = 200,
    include_hidden: bool = False,
) -> dict:
    """
    List files in the shared workspace.

    Args:
        pattern: Optional glob pattern (e.g., "*.md" or "reports/*.xlsx")
        recursive: Recurse into subdirectories
        limit: Maximum number of files to return
        include_hidden: Include dotfiles
    """
    files = _gather_files(pattern, recursive, include_hidden, limit)
    file_info = [_file_info(path) for path in files]
    file_info.sort(key=lambda f: f["path"])

    return {
        "workspace": str(WORKSPACE),
        "files": file_info,
        "count": len(file_info),
        "truncated": len(file_info) >= limit,
    }


@mcp.tool()
def read_text_file(
    path: str,
    max_bytes: int = 65536,
    include_signed_url: bool = True,
) -> dict:
    """
    Read a text file from the workspace with a safety cap.

    Args:
        path: Workspace-relative path to the file
        max_bytes: Maximum bytes to read
        include_signed_url: Return a signed download URL when available
    """
    file_path = _resolve_path(path)

    if not file_path.exists() or not file_path.is_file():
        raise ValueError(f"File not found: {path}")

    data = file_path.read_bytes()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]

    content = data.decode("utf-8", errors="replace")
    result = {
        "path": str(file_path.relative_to(WORKSPACE)),
        "size": file_path.stat().st_size,
        "content": content,
        "truncated": truncated,
    }

    if include_signed_url:
        result.update(_signed_url(file_path))

    return result


@mcp.tool()
def create_note(
    title: str,
    body: str,
    filename: Optional[str] = None,
    tags: Optional[List[str]] = None,
    folder: str = "notes",
) -> dict:
    """
    Create a markdown note in the workspace with simple front matter.

    Args:
        title: Note title
        body: Markdown body
        filename: Optional filename (auto-generated when omitted)
        tags: Optional list of tags saved in front matter
        folder: Subfolder under the workspace to place the note
    """
    safe_name = filename or re.sub(r"[^a-zA-Z0-9_-]+", "-", title.strip().lower()).strip("-")
    safe_name = safe_name or "note"
    if not safe_name.endswith(".md"):
        safe_name = f"{safe_name}.md"

    output_path = _resolve_path(os.path.join(folder, safe_name))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"
    tags_text = ", ".join(tags) if tags else ""

    content_lines = [
        "---",
        f"title: {title}",
        f"created: {timestamp}",
        f"tags: [{tags_text}]",
        "---",
        "",
        body,
        "",
    ]

    output_path.write_text("\n".join(content_lines), encoding="utf-8")
    logger.info("Created note at %s", output_path)

    result = {
        "path": str(output_path.relative_to(WORKSPACE)),
        "absolute_path": str(output_path),
        "size": output_path.stat().st_size,
    }
    result.update(_signed_url(output_path))
    return result


@mcp.resource("workspace://index")
def workspace_index() -> str:
    """Lightweight index of the first few files in the workspace."""
    files = _gather_files(pattern=None, recursive=True, include_hidden=False, limit=30)
    if not files:
        return f"Workspace {WORKSPACE} is empty."

    lines = [f"Workspace root: {WORKSPACE}", "Recent files:"]
    for path in files:
        rel = path.relative_to(WORKSPACE)
        lines.append(f"- {rel.as_posix()} ({path.stat().st_size} bytes)")

    if len(files) >= 30:
        lines.append("... truncated")
    return "\n".join(lines)


@mcp.prompt()
def summarize_file_prompt(filename: str) -> str:
    """Prompt template that nudges the model to call read_text_file before summarizing."""
    return (
        f"1) Call the read_text_file tool with path='{filename}' to load the content. "
        "2) Summarize the key points and note any action items. "
        "3) Suggest a title for a follow-up note."
    )


def build_app():
    app = mcp.streamable_http_app()

    @app.route("/healthz")
    async def healthz(_request):  # type: ignore[unused-ignore]
        return JSONResponse({"status": "ok"})

    return app


def main() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info("Starting python-sdk-mcp on %s:%s%s", HOST, PORT, STREAM_PATH)
    import uvicorn

    uvicorn.run(build_app(), host=HOST, port=PORT, log_level=LOG_LEVEL.lower())


if __name__ == "__main__":
    main()
