"""NEXUS AI Agent - Regex Tool"""

import re
from typing import List, Dict, Any, Optional, Pattern
from dataclasses import dataclass, field


@dataclass
class RegexMatch:
    """Regex match result"""
    text: str
    start: int
    end: int
    groups: tuple
    group_dict: Dict[str, str]


@dataclass
class RegexResult:
    """Regex operation result"""
    pattern: str
    input_text: str
    matches: List[RegexMatch] = field(default_factory=list)
    match_count: int = 0


class RegexTool:
    """Regular expression utilities"""

    def __init__(self):
        # Common patterns
        self._patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://[^\s]+',
            'phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'date_ymd': r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
            'date_dmy': r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',
            'time': r'\b\d{1,2}:\d{2}(?::\d{2})?\b',
            'hex_color': r'#(?:[0-9a-fA-F]{3}){1,2}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'zip_code': r'\b\d{5}(?:-\d{4})?\b',
            'username': r'^[a-zA-Z0-9_]{3,16}$',
            'password_strong': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            'slug': r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        }

    def match(
        self,
        pattern: str,
        text: str,
        flags: int = 0
    ) -> Optional[RegexMatch]:
        """
        Match pattern at start of text

        Args:
            pattern: Regex pattern
            text: Text to match
            flags: Regex flags

        Returns:
            RegexMatch or None
        """
        match = re.match(pattern, text, flags)
        if match:
            return RegexMatch(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                groups=match.groups(),
                group_dict=match.groupdict()
            )
        return None

    def search(
        self,
        pattern: str,
        text: str,
        flags: int = 0
    ) -> Optional[RegexMatch]:
        """
        Search for pattern in text

        Args:
            pattern: Regex pattern
            text: Text to search
            flags: Regex flags

        Returns:
            RegexMatch or None
        """
        match = re.search(pattern, text, flags)
        if match:
            return RegexMatch(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                groups=match.groups(),
                group_dict=match.groupdict()
            )
        return None

    def find_all(
        self,
        pattern: str,
        text: str,
        flags: int = 0
    ) -> RegexResult:
        """
        Find all matches

        Args:
            pattern: Regex pattern
            text: Text to search
            flags: Regex flags

        Returns:
            RegexResult with all matches
        """
        result = RegexResult(pattern=pattern, input_text=text)

        for match in re.finditer(pattern, text, flags):
            result.matches.append(RegexMatch(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                groups=match.groups(),
                group_dict=match.groupdict()
            ))

        result.match_count = len(result.matches)
        return result

    def replace(
        self,
        pattern: str,
        replacement: str,
        text: str,
        count: int = 0,
        flags: int = 0
    ) -> str:
        """
        Replace pattern matches

        Args:
            pattern: Regex pattern
            replacement: Replacement string
            text: Text to process
            count: Max replacements (0 = all)
            flags: Regex flags

        Returns:
            Modified text
        """
        return re.sub(pattern, replacement, text, count=count, flags=flags)

    def split(
        self,
        pattern: str,
        text: str,
        maxsplit: int = 0,
        flags: int = 0
    ) -> List[str]:
        """
        Split text by pattern

        Args:
            pattern: Regex pattern
            text: Text to split
            maxsplit: Max splits (0 = all)
            flags: Regex flags

        Returns:
            List of strings
        """
        return re.split(pattern, text, maxsplit=maxsplit, flags=flags)

    def test(self, pattern: str, text: str, flags: int = 0) -> bool:
        """
        Test if pattern matches text

        Args:
            pattern: Regex pattern
            text: Text to test
            flags: Regex flags

        Returns:
            True if pattern matches
        """
        return bool(re.search(pattern, text, flags))

    def validate(self, pattern: str) -> Dict[str, Any]:
        """
        Validate regex pattern

        Args:
            pattern: Regex pattern

        Returns:
            Dict with valid status and error
        """
        try:
            re.compile(pattern)
            return {"valid": True, "error": None}
        except re.error as e:
            return {"valid": False, "error": str(e)}

    def get_pattern(self, name: str) -> Optional[str]:
        """Get common pattern by name"""
        return self._patterns.get(name)

    def add_pattern(self, name: str, pattern: str) -> None:
        """Add custom pattern"""
        self._patterns[name] = pattern

    def list_patterns(self) -> List[str]:
        """List available pattern names"""
        return list(self._patterns.keys())

    def extract_groups(
        self,
        pattern: str,
        text: str,
        flags: int = 0
    ) -> List[tuple]:
        """
        Extract all groups from matches

        Args:
            pattern: Regex pattern with groups
            text: Text to search
            flags: Regex flags

        Returns:
            List of group tuples
        """
        return re.findall(pattern, text, flags)

    def escape(self, text: str) -> str:
        """Escape special regex characters"""
        return re.escape(text)

    def explain(self, pattern: str) -> str:
        """
        Explain regex pattern (basic)

        Args:
            pattern: Regex pattern

        Returns:
            Human-readable explanation
        """
        explanations = {
            '^': 'Start of string',
            '$': 'End of string',
            '.': 'Any character except newline',
            '*': 'Zero or more of preceding',
            '+': 'One or more of preceding',
            '?': 'Zero or one of preceding',
            '\\d': 'Any digit (0-9)',
            '\\D': 'Any non-digit',
            '\\w': 'Any word character (a-z, A-Z, 0-9, _)',
            '\\W': 'Any non-word character',
            '\\s': 'Any whitespace',
            '\\S': 'Any non-whitespace',
            '\\b': 'Word boundary',
            '|': 'OR operator',
            '[]': 'Character class',
            '()': 'Capture group',
            '(?:)': 'Non-capturing group',
            '(?=)': 'Positive lookahead',
            '(?!)': 'Negative lookahead',
        }

        parts = []
        for token, desc in explanations.items():
            if token in pattern:
                parts.append(f"  {token}: {desc}")

        if parts:
            return "Pattern elements:\n" + "\n".join(parts)
        return "No common elements found"

    # Convenience methods using common patterns
    def is_email(self, text: str) -> bool:
        """Check if text is valid email"""
        return bool(re.fullmatch(self._patterns['email'], text, re.IGNORECASE))

    def is_url(self, text: str) -> bool:
        """Check if text is valid URL"""
        return bool(re.match(self._patterns['url'], text))

    def is_phone(self, text: str) -> bool:
        """Check if text is valid phone number"""
        return bool(re.fullmatch(self._patterns['phone'], text))

    def is_ip_address(self, text: str) -> bool:
        """Check if text is valid IP address"""
        if not re.fullmatch(self._patterns['ip_address'], text):
            return False
        parts = text.split('.')
        return all(0 <= int(part) <= 255 for part in parts)

    def find_emails(self, text: str) -> List[str]:
        """Find all emails in text"""
        return re.findall(self._patterns['email'], text, re.IGNORECASE)

    def find_urls(self, text: str) -> List[str]:
        """Find all URLs in text"""
        return re.findall(self._patterns['url'], text)

    def find_phones(self, text: str) -> List[str]:
        """Find all phone numbers in text"""
        return re.findall(self._patterns['phone'], text)

