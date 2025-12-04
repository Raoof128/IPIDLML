"""
HTML Extractor

Extracts and analyzes content from HTML documents.
Detects hidden payloads, suspicious scripts, and injection patterns.
"""

import re
from html import unescape
from typing import Any, cast

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLExtractor:
    """
    HTML content extraction and analysis engine.

    Features:
    - Visible text extraction with tag stripping
    - Hidden div/element detection
    - Suspicious script identification
    - Alt-text extraction for accessibility abuse detection
    - CSS-injected text detection
    - Base64 embedded content detection
    """

    def __init__(self) -> None:
        """Initialize the HTML extractor."""
        # Patterns for detection
        self.hidden_patterns = [
            r"display\s*:\s*none",
            r"visibility\s*:\s*hidden",
            r"opacity\s*:\s*0(?:\s|;|$)",
            r"height\s*:\s*0",
            r"width\s*:\s*0",
            r"font-size\s*:\s*0",
            r"color\s*:\s*(?:transparent|rgba\(.*?,\s*0\))",
            r"position\s*:\s*absolute.*?(?:left|top)\s*:\s*-\d+",
        ]

        self.suspicious_script_patterns = [
            r"eval\s*\(",
            r"document\.write",
            r"innerHTML\s*=",
            r"outerHTML\s*=",
            r"\.src\s*=",
            r"atob\s*\(",  # Base64 decode
            r"btoa\s*\(",  # Base64 encode
            r"fromCharCode",
            r"\\x[0-9a-fA-F]{2}",  # Hex encoding
            r"\\u[0-9a-fA-F]{4}",  # Unicode encoding
        ]

        self.injection_indicators = [
            r"ignore\s+(?:all\s+)?previous",
            r"disregard\s+(?:the\s+)?above",
            r"new\s+instructions?",
            r"system\s*:\s*",
            r"assistant\s*:\s*",
            r"user\s*:\s*",
            r"override\s+(?:safety|security)",
            r"jailbreak",
            r"DAN\s+mode",
        ]

    def extract(
        self, html_content: str, extract_alt_text: bool = True, detect_hidden: bool = True
    ) -> dict[str, Any]:
        """
        Extract content from HTML.

        Args:
            html_content: Raw HTML string
            extract_alt_text: Whether to extract alt text from images
            detect_hidden: Whether to detect hidden elements

        Returns:
            dict: {
                "visible_text": extracted visible text,
                "alt_texts": list of alt texts from images,
                "has_hidden_divs": whether hidden content was found,
                "hidden_content": list of hidden content pieces,
                "has_suspicious_scripts": whether suspicious JS was found,
                "suspicious_scripts": list of suspicious script snippets,
                "base64_content": list of base64 encoded content,
                "injection_indicators": list of potential injection patterns
            }
        """
        logger.info("Starting HTML extraction")

        result = {
            "visible_text": "",
            "alt_texts": [],
            "has_hidden_divs": False,
            "hidden_content": [],
            "has_suspicious_scripts": False,
            "suspicious_scripts": [],
            "base64_content": [],
            "injection_indicators": [],
            "metadata": {},
        }

        try:
            # Try to use BeautifulSoup if available
            result = self._extract_with_beautifulsoup(html_content, extract_alt_text, detect_hidden)
        except ImportError:
            # Fallback to regex-based extraction
            result = self._extract_with_regex(html_content, extract_alt_text, detect_hidden)

        # Check for injection indicators in all extracted text
        visible_text = str(result.get("visible_text", ""))
        alt_texts = result.get("alt_texts", [])
        alt_texts_list = alt_texts if isinstance(alt_texts, list) else []
        all_text = visible_text + " " + " ".join(str(t) for t in alt_texts_list)
        result["injection_indicators"] = self._detect_injection_patterns(all_text)

        return result

    def _extract_with_beautifulsoup(
        self, html_content: str, extract_alt_text: bool, detect_hidden: bool
    ) -> dict[str, Any]:
        """Extract using BeautifulSoup parser."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        result = {
            "visible_text": "",
            "alt_texts": [],
            "has_hidden_divs": False,
            "hidden_content": [],
            "has_suspicious_scripts": False,
            "suspicious_scripts": [],
            "base64_content": [],
            "injection_indicators": [],
            "metadata": {},
        }

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata = cast(dict[str, Any], result["metadata"])
            metadata["title"] = title_tag.get_text(strip=True)

        # Remove script and style elements for visible text extraction
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        # Get visible text
        result["visible_text"] = soup.get_text(separator=" ", strip=True)

        # Re-parse for script analysis
        soup_full = BeautifulSoup(html_content, "html.parser")

        # Extract alt texts
        if extract_alt_text:
            for img in soup_full.find_all("img"):
                alt = img.get("alt", "")
                if alt:
                    alt_texts_list = cast(list[str], result["alt_texts"])
                    alt_texts_list.append(alt)

        # Detect hidden content
        if detect_hidden:
            hidden_elements = self._find_hidden_elements(soup_full)
            result["has_hidden_divs"] = len(hidden_elements) > 0
            result["hidden_content"] = hidden_elements

        # Analyze scripts
        scripts = soup_full.find_all("script")
        for script in scripts:
            script_text = script.string or ""
            suspicious = self._analyze_script(script_text)
            if suspicious:
                result["has_suspicious_scripts"] = True
                scripts_list = cast(list[dict[str, Any]], result["suspicious_scripts"])
                scripts_list.append({"snippet": script_text[:200], "patterns_found": suspicious})

        # Detect base64 content
        result["base64_content"] = self._detect_base64(html_content)

        return result

    def _extract_with_regex(
        self, html_content: str, extract_alt_text: bool, detect_hidden: bool
    ) -> dict[str, Any]:
        """Fallback regex-based extraction."""
        result = {
            "visible_text": "",
            "alt_texts": [],
            "has_hidden_divs": False,
            "hidden_content": [],
            "has_suspicious_scripts": False,
            "suspicious_scripts": [],
            "base64_content": [],
            "injection_indicators": [],
            "metadata": {},
        }

        # Remove scripts and styles
        text = re.sub(
            r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = unescape(text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        result["visible_text"] = text

        # Extract alt texts
        if extract_alt_text:
            alt_matches = re.findall(r'alt\s*=\s*["\']([^"\']*)["\']', html_content, re.IGNORECASE)
            result["alt_texts"] = alt_matches

        # Detect hidden patterns
        if detect_hidden:
            for pattern in self.hidden_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    result["has_hidden_divs"] = True
                    hidden_list = cast(list[dict[str, Any]], result["hidden_content"])
                    hidden_list.append({"pattern": pattern, "type": "style_based_hiding"})

        # Check for suspicious scripts
        script_matches = re.findall(
            r"<script[^>]*>(.*?)</script>", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        for script in script_matches:
            suspicious = self._analyze_script(script)
            if suspicious:
                result["has_suspicious_scripts"] = True
                scripts_list = cast(list[dict[str, Any]], result["suspicious_scripts"])
                scripts_list.append({"snippet": script[:200], "patterns_found": suspicious})

        # Detect base64
        result["base64_content"] = self._detect_base64(html_content)

        return result

    def _find_hidden_elements(self, soup: Any) -> list[dict[str, Any]]:
        """Find elements with hidden styles."""
        hidden = []

        # Check inline styles
        for element in soup.find_all(style=True):
            style = element.get("style", "")
            for pattern in self.hidden_patterns:
                if re.search(pattern, style, re.IGNORECASE):
                    text = element.get_text(strip=True)
                    if text:
                        hidden.append(
                            {
                                "tag": element.name,
                                "text": text[:100],
                                "hiding_method": pattern,
                                "full_style": style[:100],
                            }
                        )
                    break

        # Check for elements with hidden class
        for element in soup.find_all(class_=re.compile(r"hidden|invisible|sr-only", re.IGNORECASE)):
            text = element.get_text(strip=True)
            if text:
                hidden.append(
                    {
                        "tag": element.name,
                        "text": text[:100],
                        "hiding_method": "class_based",
                        "class": element.get("class", []),
                    }
                )

        return hidden

    def _analyze_script(self, script_text: str) -> list[str]:
        """Analyze script for suspicious patterns."""
        found_patterns = []

        for pattern in self.suspicious_script_patterns:
            if re.search(pattern, script_text, re.IGNORECASE):
                found_patterns.append(pattern)

        return found_patterns

    def _detect_base64(self, content: str) -> list[dict]:
        """Detect base64 encoded content."""
        base64_pattern = r"(?:data:[^;]+;base64,)?([A-Za-z0-9+/]{40,}={0,2})"
        matches = re.findall(base64_pattern, content)

        results = []
        for match in matches[:5]:  # Limit to first 5
            results.append(
                {
                    "preview": match[:50] + "..." if len(match) > 50 else match,
                    "length": len(match),
                    "decoded_preview": self._safe_decode_base64(match),
                }
            )

        return results

    def _safe_decode_base64(self, encoded: str) -> str:
        """Safely decode base64 for preview."""
        import base64

        try:
            decoded = base64.b64decode(encoded).decode("utf-8", errors="replace")
            return decoded[:100] if len(decoded) > 100 else decoded
        except Exception:
            return "[Unable to decode]"

    def _detect_injection_patterns(self, text: str) -> list[dict]:
        """Detect injection indicator patterns in text."""
        found = []

        for pattern in self.injection_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found.append(
                    {
                        "pattern": pattern,
                        "matched_text": match.group(),
                        "position": match.start(),
                        "severity": (
                            "high" if "override" in pattern or "jailbreak" in pattern else "medium"
                        ),
                    }
                )

        return found

    def strip_dangerous_elements(self, html_content: str) -> str:
        """
        Strip potentially dangerous elements from HTML.

        Removes:
        - All script tags
        - All style tags with suspicious content
        - Event handlers (onclick, onload, etc.)
        - Hidden elements
        """
        # Remove scripts
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove event handlers
        cleaned = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", cleaned, flags=re.IGNORECASE)

        # Remove javascript: links
        cleaned = re.sub(
            r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', cleaned, flags=re.IGNORECASE
        )

        return cleaned
