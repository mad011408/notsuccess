"""NEXUS AI Agent - File Reader"""

import os
import mimetypes
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileContent:
    """File content result"""
    path: str
    content: str
    encoding: str
    size: int
    mime_type: Optional[str] = None
    lines: int = 0
    error: Optional[str] = None


class FileReader:
    """Read files with various options"""

    def __init__(self, max_size: int = 10 * 1024 * 1024):  # 10MB default
        self.max_size = max_size
        self._encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']

    def read(
        self,
        path: str,
        encoding: Optional[str] = None,
        lines: Optional[tuple] = None
    ) -> FileContent:
        """
        Read file content

        Args:
            path: File path
            encoding: Force specific encoding
            lines: Tuple of (start, end) line numbers

        Returns:
            FileContent object
        """
        path = os.path.abspath(path)

        if not os.path.exists(path):
            return FileContent(
                path=path,
                content="",
                encoding="",
                size=0,
                error=f"File not found: {path}"
            )

        if not os.path.isfile(path):
            return FileContent(
                path=path,
                content="",
                encoding="",
                size=0,
                error=f"Not a file: {path}"
            )

        size = os.path.getsize(path)
        if size > self.max_size:
            return FileContent(
                path=path,
                content="",
                encoding="",
                size=size,
                error=f"File too large: {size} bytes > {self.max_size} bytes"
            )

        mime_type = mimetypes.guess_type(path)[0]

        # Try to read with specified or detected encoding
        content = None
        used_encoding = encoding

        if encoding:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                pass

        if content is None:
            for enc in self._encodings:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        content = f.read()
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue

        if content is None:
            # Read as binary
            with open(path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
            used_encoding = 'binary'

        # Apply line filter
        if lines and content:
            content_lines = content.split('\n')
            start, end = lines
            content = '\n'.join(content_lines[start:end])

        line_count = content.count('\n') + 1 if content else 0

        return FileContent(
            path=path,
            content=content,
            encoding=used_encoding or 'unknown',
            size=size,
            mime_type=mime_type,
            lines=line_count
        )

    def read_lines(
        self,
        path: str,
        start: int = 0,
        count: Optional[int] = None
    ) -> List[str]:
        """Read specific lines from file"""
        result = self.read(path)
        if result.error:
            return []

        lines = result.content.split('\n')
        if count:
            return lines[start:start + count]
        return lines[start:]

    def read_head(self, path: str, lines: int = 10) -> str:
        """Read first N lines"""
        return '\n'.join(self.read_lines(path, 0, lines))

    def read_tail(self, path: str, lines: int = 10) -> str:
        """Read last N lines"""
        result = self.read(path)
        if result.error:
            return ""
        all_lines = result.content.split('\n')
        return '\n'.join(all_lines[-lines:])

    def read_binary(self, path: str) -> bytes:
        """Read file as binary"""
        with open(path, 'rb') as f:
            return f.read()

    def read_json(self, path: str) -> Dict[str, Any]:
        """Read JSON file"""
        import json
        result = self.read(path)
        if result.error:
            return {}
        return json.loads(result.content)

    def read_yaml(self, path: str) -> Dict[str, Any]:
        """Read YAML file"""
        try:
            import yaml
            result = self.read(path)
            if result.error:
                return {}
            return yaml.safe_load(result.content) or {}
        except ImportError:
            return {}

    def get_info(self, path: str) -> Dict[str, Any]:
        """Get file information"""
        path = os.path.abspath(path)

        if not os.path.exists(path):
            return {"error": "File not found"}

        stat = os.stat(path)
        return {
            "path": path,
            "name": os.path.basename(path),
            "extension": os.path.splitext(path)[1],
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "mime_type": mimetypes.guess_type(path)[0],
        }

    def exists(self, path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(path)

    def is_text_file(self, path: str) -> bool:
        """Check if file is text"""
        mime = mimetypes.guess_type(path)[0]
        if mime:
            return mime.startswith('text/') or mime in [
                'application/json',
                'application/xml',
                'application/javascript'
            ]
        # Try to read first bytes
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                return not bool(chunk.translate(None, bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))))
        except:
            return False

