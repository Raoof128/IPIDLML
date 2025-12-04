"""
Sanitizer Engine - Neutralizes detected prompt injection payloads.
"""

import re
from enum import Enum
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SanitizationMode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


class Sanitizer:
    """Content sanitization engine for neutralizing prompt injections."""

    def __init__(self):
        self.replacement_map = {
            r"\bignore\s+(?:all\s+)?previous\s+instructions?\b": "[FILTERED: instruction override attempt]",
            r"\bdisregard\s+(?:the\s+)?(?:above|safety|rules?)\b": "[FILTERED: safety bypass attempt]",
            r"\bjailbreak\b": "[FILTERED]",
            r"\bDAN\s*mode\b": "[FILTERED]",
            r"\bforget\s+everything\b": "[FILTERED: memory manipulation]",
            r"\byou\s+are\s+now\b": "[FILTERED: role change attempt]",
            r"\bsystem\s*:\s*override\b": "[FILTERED: system override]",
            r"\badmin\s*:\s*": "[FILTERED: admin impersonation]",
        }

    def sanitize(
        self,
        content: str,
        mode: SanitizationMode = SanitizationMode.BALANCED,
        custom_patterns: Optional[list[str]] = None,
        preserve_semantics: bool = True,
    ) -> dict:
        logger.info(f"Sanitizing content in {mode.value} mode")

        if mode == SanitizationMode.PERMISSIVE:
            return {
                "sanitized_content": content,
                "segments_modified": 0,
                "segments": [],
                "warnings": ["Permissive mode - content passed without modification"],
            }

        sanitized = content
        segments = []

        for pattern, replacement in self.replacement_map.items():
            matches = list(re.finditer(pattern, sanitized, re.IGNORECASE))
            for match in reversed(matches):
                original = match.group()
                if mode == SanitizationMode.STRICT:
                    new_text = "[BLOCKED]"
                else:
                    new_text = replacement if preserve_semantics else "[REMOVED]"

                segments.append(
                    {
                        "original": original,
                        "sanitized": new_text,
                        "start": match.start(),
                        "end": match.end(),
                        "action": "replaced",
                        "reason": f"Matched dangerous pattern: {pattern[:30]}...",
                    }
                )
                sanitized = sanitized[: match.start()] + new_text + sanitized[match.end() :]

        if custom_patterns:
            for pattern in custom_patterns:
                try:
                    matches = list(re.finditer(pattern, sanitized, re.IGNORECASE))
                    for match in reversed(matches):
                        segments.append(
                            {
                                "original": match.group(),
                                "sanitized": "[CUSTOM_FILTER]",
                                "start": match.start(),
                                "end": match.end(),
                                "action": "replaced",
                                "reason": "Custom pattern match",
                            }
                        )
                        sanitized = (
                            sanitized[: match.start()]
                            + "[CUSTOM_FILTER]"
                            + sanitized[match.end() :]
                        )
                except re.error:
                    logger.warning(f"Invalid custom pattern: {pattern}")

        return {
            "sanitized_content": sanitized,
            "segments_modified": len(segments),
            "segments": segments,
            "warnings": [],
        }

    def escape_llm_triggers(self, text: str) -> str:
        """Escape common LLM trigger patterns."""
        escapes = [
            (r"\n", " "),
            (r"\r", " "),
            (r"```", "` ` `"),
            (r"<\|", "< |"),
            (r"\|>", "| >"),
        ]
        result = text
        for pattern, replacement in escapes:
            result = result.replace(pattern, replacement)
        return result
