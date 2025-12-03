"""
Simple HTTP server for serving files via signed download URLs.

This service validates signed URLs and serves files securely.
"""
import logging
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from aiohttp import web

# Add parent directory to path for shared module
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.download_urls import verify_signature

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("download-service")

PORT = int(os.getenv("DOWNLOAD_SERVICE_PORT", "8080"))


async def handle_download(request):
    """Handle download requests with signature verification."""
    try:
        # Parse query parameters
        file_path = request.query.get("file")
        expires_str = request.query.get("expires")
        filename = request.query.get("filename")
        signature = request.query.get("signature")

        # Validate all required parameters
        if not all([file_path, expires_str, filename, signature]):
            logger.warning("Missing required parameters in download request")
            return web.Response(
                text="Missing required parameters",
                status=400
            )

        expires_at = int(expires_str)

        # Verify signature
        if not verify_signature(file_path, expires_at, filename, signature):
            logger.warning(f"Invalid or expired signature for file: {file_path}")
            return web.Response(
                text="Invalid or expired download link",
                status=403
            )

        # Check if file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"File not found: {file_path}")
            return web.Response(
                text="File not found",
                status=404
            )

        # Serve the file
        logger.info(f"Serving file: {file_path} as {filename}")

        return web.FileResponse(
            path=file_path,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"Error handling download: {str(e)}")
        return web.Response(
            text="Internal server error",
            status=500
        )


async def handle_health(request):
    """Health check endpoint."""
    return web.json_response({"status": "healthy"})


def create_app():
    """Create and configure the aiohttp application."""
    app = web.Application()
    app.router.add_get("/download", handle_download)
    app.router.add_get("/health", handle_health)
    return app


if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting download service on port {PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
