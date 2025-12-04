"""
Text Utilities - Common text processing functions.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for consistent processing."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)


def detect_encoding_patterns(text: str) -> dict:
    """Detect potential encoding obfuscation."""
    return {
        "has_base64": bool(re.search(r"[A-Za-z0-9+/]{20,}={0,2}", text)),
        "has_hex": bool(re.search(r"(?:\\x[0-9a-fA-F]{2}){3,}", text)),
        "has_unicode_escapes": bool(re.search(r"(?:\\u[0-9a-fA-F]{4}){2,}", text)),
        "has_url_encoding": bool(re.search(r"(?:%[0-9a-fA-F]{2}){3,}", text)),
    }


def truncate_for_display(text: str, max_length: int = 200) -> str:
    """Truncate text for display with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
