"""NEXUS AI Agent - File Writer"""

import os
import shutil
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WriteResult:
    """Result of write operation"""
    success: bool
    path: str
    bytes_written: int = 0
    error: Optional[str] = None
    backup_path: Optional[str] = None


class FileWriter:
    """Write files with various options"""

    def __init__(self, create_backup: bool = True, backup_dir: Optional[str] = None):
        self.create_backup = create_backup
        self.backup_dir = backup_dir

    def write(
        self,
        path: str,
        content: str,
        encoding: str = 'utf-8',
        mode: str = 'w',
        create_dirs: bool = True
    ) -> WriteResult:
        """
        Write content to file

        Args:
            path: File path
            content: Content to write
            encoding: File encoding
            mode: Write mode ('w' or 'a')
            create_dirs: Create parent directories if needed

        Returns:
            WriteResult
        """
        path = os.path.abspath(path)

        try:
            # Create backup if file exists
            backup_path = None
            if self.create_backup and os.path.exists(path):
                backup_path = self._create_backup(path)

            # Create parent directories
            if create_dirs:
                os.makedirs(os.path.dirname(path), exist_ok=True)

            # Write content
            with open(path, mode, encoding=encoding) as f:
                f.write(content)

            return WriteResult(
                success=True,
                path=path,
                bytes_written=len(content.encode(encoding)),
                backup_path=backup_path
            )

        except Exception as e:
            return WriteResult(
                success=False,
                path=path,
                error=str(e)
            )

    def write_lines(
        self,
        path: str,
        lines: List[str],
        encoding: str = 'utf-8'
    ) -> WriteResult:
        """Write lines to file"""
        content = '\n'.join(lines)
        return self.write(path, content, encoding)

    def append(self, path: str, content: str, encoding: str = 'utf-8') -> WriteResult:
        """Append to file"""
        return self.write(path, content, encoding, mode='a')

    def write_binary(self, path: str, data: bytes) -> WriteResult:
        """Write binary data"""
        path = os.path.abspath(path)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)

            return WriteResult(
                success=True,
                path=path,
                bytes_written=len(data)
            )
        except Exception as e:
            return WriteResult(
                success=False,
                path=path,
                error=str(e)
            )

    def write_json(
        self,
        path: str,
        data: Dict[str, Any],
        indent: int = 2
    ) -> WriteResult:
        """Write JSON file"""
        import json
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return self.write(path, content)

    def write_yaml(self, path: str, data: Dict[str, Any]) -> WriteResult:
        """Write YAML file"""
        try:
            import yaml
            content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            return self.write(path, content)
        except ImportError:
            return WriteResult(
                success=False,
                path=path,
                error="PyYAML not installed"
            )

    def copy(self, src: str, dst: str, overwrite: bool = False) -> WriteResult:
        """Copy file"""
        src = os.path.abspath(src)
        dst = os.path.abspath(dst)

        try:
            if not os.path.exists(src):
                return WriteResult(
                    success=False,
                    path=dst,
                    error=f"Source not found: {src}"
                )

            if os.path.exists(dst) and not overwrite:
                return WriteResult(
                    success=False,
                    path=dst,
                    error="Destination exists and overwrite=False"
                )

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

            return WriteResult(
                success=True,
                path=dst,
                bytes_written=os.path.getsize(dst)
            )
        except Exception as e:
            return WriteResult(
                success=False,
                path=dst,
                error=str(e)
            )

    def move(self, src: str, dst: str, overwrite: bool = False) -> WriteResult:
        """Move file"""
        src = os.path.abspath(src)
        dst = os.path.abspath(dst)

        try:
            if not os.path.exists(src):
                return WriteResult(
                    success=False,
                    path=dst,
                    error=f"Source not found: {src}"
                )

            if os.path.exists(dst) and not overwrite:
                return WriteResult(
                    success=False,
                    path=dst,
                    error="Destination exists and overwrite=False"
                )

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

            return WriteResult(
                success=True,
                path=dst
            )
        except Exception as e:
            return WriteResult(
                success=False,
                path=dst,
                error=str(e)
            )

    def delete(self, path: str, create_backup: bool = True) -> WriteResult:
        """Delete file"""
        path = os.path.abspath(path)

        try:
            if not os.path.exists(path):
                return WriteResult(
                    success=False,
                    path=path,
                    error="File not found"
                )

            backup_path = None
            if create_backup:
                backup_path = self._create_backup(path)

            os.remove(path)

            return WriteResult(
                success=True,
                path=path,
                backup_path=backup_path
            )
        except Exception as e:
            return WriteResult(
                success=False,
                path=path,
                error=str(e)
            )

    def _create_backup(self, path: str) -> str:
        """Create backup of file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(path)

        if self.backup_dir:
            os.makedirs(self.backup_dir, exist_ok=True)
            backup_path = os.path.join(self.backup_dir, f"{filename}.{timestamp}.bak")
        else:
            backup_path = f"{path}.{timestamp}.bak"

        shutil.copy2(path, backup_path)
        return backup_path

    def touch(self, path: str) -> WriteResult:
        """Create empty file or update timestamp"""
        path = os.path.abspath(path)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a'):
                os.utime(path, None)

            return WriteResult(
                success=True,
                path=path
            )
        except Exception as e:
            return WriteResult(
                success=False,
                path=path,
                error=str(e)
            )

