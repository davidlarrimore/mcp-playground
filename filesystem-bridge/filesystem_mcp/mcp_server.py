import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import anyio
import pandas as pd
from mcp.server.fastmcp import FastMCP

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("filesystem-mcp")

ROOT = Path(os.getenv("FILESYSTEM_ROOT", "/demo-data")).resolve()

server = FastMCP("filesystem-mcp")


@server.tool()
async def list_allowed_directories() -> List[str]:
    """
    Return the root directory that this server allows access to.
    """

    return [str(ROOT)]


@server.tool()
async def list_directory(path: str = ".") -> List[dict]:
    """
    Alias for list_dir (kept for client compatibility).
    """

    return await list_dir(path=path)


def _resolve_path(path: str) -> Path:
    """Resolve a user-supplied path under the configured root and block escapes."""
    # Normalize common root variants
    if path in ("", ".", "/"):
        candidate = ROOT
    else:
        candidate_path = Path(path)
        if candidate_path.is_absolute():
            candidate = candidate_path.resolve()
        else:
            candidate = (ROOT / path).resolve()

    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"Path escapes root: {path}") from exc
    if not candidate.exists():
        raise FileNotFoundError(f"Path not found: {candidate}")
    return candidate


def _guess_header_row(df_raw: pd.DataFrame, sample_rows: int = 25) -> int:
    """Pick a likely header row by the densest early row."""
    best_row = 0
    best_score = -1
    for idx, row in df_raw.head(sample_rows).iterrows():
        non_null = row.count()
        if non_null == 0:
            continue
        string_bonus = 0.5 if any(isinstance(v, str) for v in row) else 0
        score = non_null + string_bonus
        if score > best_score:
            best_score = score
            best_row = idx
    return int(best_row)


@server.tool()
async def list_dir(path: str = ".") -> List[dict]:
    """
    List files and directories under the given path (relative to FILESYSTEM_ROOT).
    """

    target = _resolve_path(path)
    if not target.is_dir():
        raise ValueError(f"Not a directory: {target}")

    def _scan() -> List[dict]:
        entries: List[dict] = []
        for entry in sorted(target.iterdir(), key=lambda p: p.name):
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry.relative_to(ROOT)),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        return entries

    return await anyio.to_thread.run_sync(_scan)


@server.tool()
async def read_text(path: str, encoding: str = "utf-8", max_bytes: int = 2_000_000) -> str:
    """
    Read a text file (relative to FILESYSTEM_ROOT) with safe size limits.
    """

    full = _resolve_path(path)
    if full.is_dir():
        raise ValueError(f"Path is a directory: {full}")

    def _read() -> str:
        data = full.read_bytes()
        if len(data) > max_bytes:
            raise ValueError(f"File is too large ({len(data)} bytes > {max_bytes})")
        return data.decode(encoding, errors="replace")

    return await anyio.to_thread.run_sync(_read)


@server.tool()
async def read_file(
    path: str,
    encoding: str = "utf-8",
    max_bytes: int = 2_000_000,
    parse_excel: bool = True,
    header_row: Optional[int] = None,
    sheet: Optional[str] = None,
) -> dict:
    """
    Generic file reader. Text files are returned as text. Excel files can be parsed to markdown.
    """

    full = _resolve_path(path)

    # Excel handling
    if parse_excel and full.suffix.lower() in {".xlsx", ".xls"}:
        table = await read_excel_table(
            path=path,
            sheet=sheet,
            header_row=header_row,
        )
        return {
            "type": "excel",
            "path": str(full),
            "markdown": table["markdown"],
            "columns": table["columns"],
            "rows": table["rows"],
            "header_row": table["header_row"],
            "sheet": table["sheet"],
        }

    # Fallback to text
    text = await read_text(path=path, encoding=encoding, max_bytes=max_bytes)
    return {"type": "text", "path": str(full), "text": text}


@server.tool()
async def read_excel_table(
    path: str,
    sheet: Optional[str] = None,
    header_row: Optional[int] = None,
    max_rows: int = 1000,
    drop_unnamed: bool = True,
) -> dict:
    """
    Parse an Excel sheet into structured rows and markdown.
    """

    full = _resolve_path(path)
    if full.is_dir():
        raise ValueError(f"Path is a directory: {full}")

    def _parse() -> dict:
        sheet_name = sheet if sheet is not None else 0
        df_raw = pd.read_excel(full, sheet_name=sheet_name, header=None)
        hdr = header_row if header_row is not None else _guess_header_row(df_raw)

        logger.debug("Using header row %s for %s", hdr, full)
        df = pd.read_excel(full, sheet_name=sheet_name, header=hdr)

        if drop_unnamed:
            df = df[[c for c in df.columns if not str(c).startswith("Unnamed")]]

        df = df.dropna(how="all")

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col]).dt.date

        if max_rows:
            df = df.head(max_rows)

        columns = [str(c) for c in df.columns]
        rows = df.to_dict(orient="records")
        markdown = df.to_markdown(index=False)
        return {
            "columns": columns,
            "rows": rows,
            "markdown": markdown,
            "header_row": hdr,
            "sheet": sheet_name,
        }

    return await anyio.to_thread.run_sync(_parse)


if __name__ == "__main__":
    # FastMCP.run handles its own event loop when given a transport name.
    server.run("stdio")
