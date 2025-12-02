import base64
import binascii
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import anyio
import pandas as pd
from mcp.server.fastmcp import FastMCP

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("filesystem-mcp")

ROOT = Path(os.getenv("FILESYSTEM_ROOT", "/docs")).resolve()

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


def _resolve_new_path(path: str, create_parents: bool) -> Path:
    """
    Resolve a path for writing under ROOT. Creates parent directories if requested.
    """

    if path in ("", ".", "/"):
        raise ValueError("Provide a file path under the allowed root, not the root itself")

    candidate_path = Path(path)
    if candidate_path.is_absolute():
        candidate = candidate_path.resolve()
    else:
        candidate = (ROOT / path).resolve()

    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"Path escapes root: {path}") from exc

    parent = candidate.parent
    if not parent.exists():
        if create_parents:
            parent.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(f"Parent directory does not exist: {parent}")
    elif not parent.is_dir():
        raise ValueError(f"Parent path is not a directory: {parent}")

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
    sheet: Optional[Union[str, int]] = None,
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
async def create_file(
    path: str,
    content_base64: Optional[str] = None,
    text: Optional[str] = None,
    encoding: str = "utf-8",
    overwrite: bool = True,
    create_parents: bool = True,
    max_bytes: int = 10_000_000,
) -> dict:
    """
    Create or overwrite a file under FILESYSTEM_ROOT.
    Provide either `content_base64` for binary data (e.g., PDFs) or `text` to be encoded with `encoding`.
    """

    if (content_base64 is None and text is None) or (
        content_base64 is not None and text is not None
    ):
        raise ValueError("Provide either content_base64 or text, but not both")

    target = _resolve_new_path(path, create_parents=create_parents)

    def _write() -> dict:
        existed = target.exists()
        if target.exists() and target.is_dir():
            raise ValueError(f"Path is a directory: {target}")
        if target.exists() and not overwrite:
            raise ValueError(f"File already exists and overwrite is False: {target}")

        if text is not None:
            raw = text.encode(encoding)
        else:
            try:
                raw = base64.b64decode(content_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("content_base64 must be valid base64-encoded data") from exc

        if len(raw) > max_bytes:
            raise ValueError(f"Content too large ({len(raw)} bytes > {max_bytes})")

        target.write_bytes(raw)
        stat = target.stat()
        return {
            "path": str(target.relative_to(ROOT)),
            "absolute_path": str(target),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": not existed,
        }

    return await anyio.to_thread.run_sync(_write)


@server.tool()
async def read_excel_table(
    path: str,
    sheet: Optional[Union[str, int]] = None,
    header_row: Optional[int] = None,
    max_rows: int = 1000,
    drop_unnamed: bool = True,
) -> dict:
    """
    Parse an Excel sheet (by name or index) into structured rows and markdown.
    """

    full = _resolve_path(path)
    if full.is_dir():
        raise ValueError(f"Path is a directory: {full}")

    def _parse() -> dict:
        # Validate the requested sheet against available names/indices to give clearer errors.
        xls = pd.ExcelFile(full)
        available = xls.sheet_names

        if sheet is None:
            sheet_name = available[0] if available else 0
        elif isinstance(sheet, int):
            if sheet < 0 or sheet >= len(available):
                raise ValueError(
                    f"Sheet index {sheet} out of range. Available sheets: {available}"
                )
            sheet_name = sheet
        elif isinstance(sheet, str):
            if sheet not in available:
                raise ValueError(
                    f"Worksheet named '{sheet}' not found. Available sheets: {available}"
                )
            sheet_name = sheet
        else:
            raise ValueError(
                f"Unsupported sheet type {type(sheet)}. Provide a name or index."
            )

        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        hdr = header_row if header_row is not None else _guess_header_row(df_raw)

        logger.debug("Using header row %s for %s", hdr, full)
        df = pd.read_excel(xls, sheet_name=sheet_name, header=hdr)

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
