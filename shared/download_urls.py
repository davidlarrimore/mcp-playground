"""
Shared utility for generating signed download URLs for files.

This module provides HMAC-based signed URLs with expiration timestamps
to securely share generated documents.
"""
import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode


# Secret key for signing URLs - should be set via environment variable
SECRET_KEY = os.getenv("DOWNLOAD_URL_SECRET", "change-me-in-production")

# Base URL for the download service
DOWNLOAD_BASE_URL = os.getenv("DOWNLOAD_BASE_URL", "http://localhost:8080")

# Default expiration time in seconds (24 hours)
DEFAULT_EXPIRATION = int(os.getenv("DOWNLOAD_URL_EXPIRATION", "86400"))


def generate_signed_url(
    file_path: str,
    expiration_seconds: Optional[int] = None,
    filename: Optional[str] = None
) -> dict:
    """
    Generate a signed download URL for a file.

    Args:
        file_path: Absolute path to the file
        expiration_seconds: How long the URL is valid (seconds). Defaults to 24 hours.
        filename: Optional custom filename for download (defaults to original filename)

    Returns:
        Dictionary with:
            - url: The signed download URL
            - expires_at: Unix timestamp when URL expires
            - expires_in: Seconds until expiration
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Calculate expiration
    exp_seconds = expiration_seconds or DEFAULT_EXPIRATION
    expires_at = int(time.time()) + exp_seconds

    # Use custom filename or original
    download_filename = filename or file_path_obj.name

    # Create the message to sign: filepath|expires_at|filename
    message = f"{file_path}|{expires_at}|{download_filename}"

    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Build query parameters
    params = {
        "file": file_path,
        "expires": expires_at,
        "filename": download_filename,
        "signature": signature
    }

    # Construct the signed URL
    signed_url = f"{DOWNLOAD_BASE_URL}/download?{urlencode(params)}"

    return {
        "url": signed_url,
        "expires_at": expires_at,
        "expires_in": exp_seconds
    }


def verify_signature(file_path: str, expires_at: int, filename: str, signature: str) -> bool:
    """
    Verify a signed URL's signature.

    Args:
        file_path: The file path from the URL
        expires_at: Expiration timestamp from the URL
        filename: Filename from the URL
        signature: The signature to verify

    Returns:
        True if signature is valid and not expired, False otherwise
    """
    # Check if expired
    if time.time() > expires_at:
        return False

    # Recreate the message and signature
    message = f"{file_path}|{expires_at}|{filename}"
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)
