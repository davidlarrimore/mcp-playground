import logging
import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from weasyprint import HTML, CSS

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("pdf-mcp")

WORKSPACE = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

mcp = FastMCP("pdf")

@mcp.tool
async def save_uploaded_file(
    filename: str,
    content_base64: str
) -> dict:
    """
    Save an uploaded file (provided as base64) to the workspace.

    This is a convenience tool for when users upload files via chat.
    After saving, the file will be accessible to all workspace tools.

    IMPORTANT: Preserve the original file extension! If user uploads "data.xlsx",
    save it as "data.xlsx" (or similar .xlsx name), NOT as "data.txt".

    Args:
        filename: Name to save the file as - MUST keep original file extension
        content_base64: Base64-encoded file content from uploaded file
    """
    import base64

    try:
        file_data = base64.b64decode(content_base64)
        output_path = WORKSPACE / filename
        output_path.write_bytes(file_data)

        logger.info(f"Saved uploaded file: {output_path}")

        return {
            "path": str(output_path.relative_to(WORKSPACE)),
            "absolute_path": str(output_path),
            "size": output_path.stat().st_size,
            "message": f"File saved successfully as '{filename}'"
        }
    except Exception as e:
        error_msg = f"Error saving file: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool
async def create_pdf_from_html(
    html_content: str,
    output_filename: str,
    css: Optional[str] = None
) -> dict:
    """
    Create a PDF from HTML content.

    Args:
        html_content: HTML content or path to HTML file (relative to workspace)
        output_filename: Name of output PDF file
        css: Optional CSS stylesheet content for styling
    """
    output_path = WORKSPACE / output_filename

    # Check if html_content is a file path
    html_file = WORKSPACE / html_content
    if html_file.exists() and html_file.is_file():
        html = HTML(filename=str(html_file))
    else:
        html = HTML(string=html_content)

    stylesheets = []
    if css:
        stylesheets.append(CSS(string=css))

    html.write_pdf(output_path, stylesheets=stylesheets)

    logger.info(f"Created PDF: {output_path}")

    return {
        "path": str(output_path.relative_to(WORKSPACE)),
        "absolute_path": str(output_path),
        "size": output_path.stat().st_size
    }

if __name__ == "__main__":
    mcp.run()
