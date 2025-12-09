"""NEXUS AI Agent - Directory Tool"""

import os
import shutil
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DirectoryEntry:
    """Directory entry"""
    name: str
    path: str
    is_file: bool
    is_dir: bool
    size: int = 0
    modified: float = 0


@dataclass
class DirectoryResult:
    """Directory operation result"""
    success: bool
    path: str
    entries: List[DirectoryEntry] = field(default_factory=list)
    error: Optional[str] = None


class DirectoryTool:
    """Directory operations tool"""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getcwd()

    def list(
        self,
        path: Optional[str] = None,
        recursive: bool = False,
        include_hidden: bool = False,
        pattern: Optional[str] = None
    ) -> DirectoryResult:
        """
        List directory contents

        Args:
            path: Directory path (defaults to base_path)
            recursive: List recursively
            include_hidden: Include hidden files
            pattern: Glob pattern filter

        Returns:
            DirectoryResult
        """
        path = os.path.abspath(path or self.base_path)

        if not os.path.exists(path):
            return DirectoryResult(
                success=False,
                path=path,
                error="Directory not found"
            )

        if not os.path.isdir(path):
            return DirectoryResult(
                success=False,
                path=path,
                error="Not a directory"
            )

        entries = []

        try:
            if recursive:
                for root, dirs, files in os.walk(path):
                    # Filter hidden
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]

                    for name in dirs + files:
                        full_path = os.path.join(root, name)
                        if pattern and not Path(full_path).match(pattern):
                            continue
                        entries.append(self._create_entry(full_path))
            else:
                for name in os.listdir(path):
                    if not include_hidden and name.startswith('.'):
                        continue

                    full_path = os.path.join(path, name)
                    if pattern and not Path(full_path).match(pattern):
                        continue
                    entries.append(self._create_entry(full_path))

            return DirectoryResult(
                success=True,
                path=path,
                entries=entries
            )

        except Exception as e:
            return DirectoryResult(
                success=False,
                path=path,
                error=str(e)
            )

    def _create_entry(self, path: str) -> DirectoryEntry:
        """Create directory entry"""
        stat = os.stat(path)
        return DirectoryEntry(
            name=os.path.basename(path),
            path=path,
            is_file=os.path.isfile(path),
            is_dir=os.path.isdir(path),
            size=stat.st_size,
            modified=stat.st_mtime
        )

    def create(self, path: str, parents: bool = True) -> DirectoryResult:
        """Create directory"""
        path = os.path.abspath(path)

        try:
            if parents:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)

            return DirectoryResult(
                success=True,
                path=path
            )
        except Exception as e:
            return DirectoryResult(
                success=False,
                path=path,
                error=str(e)
            )

    def delete(
        self,
        path: str,
        recursive: bool = False,
        force: bool = False
    ) -> DirectoryResult:
        """Delete directory"""
        path = os.path.abspath(path)

        try:
            if not os.path.exists(path):
                return DirectoryResult(
                    success=False,
                    path=path,
                    error="Directory not found"
                )

            if recursive or force:
                shutil.rmtree(path)
            else:
                os.rmdir(path)

            return DirectoryResult(
                success=True,
                path=path
            )
        except Exception as e:
            return DirectoryResult(
                success=False,
                path=path,
                error=str(e)
            )

    def copy(self, src: str, dst: str) -> DirectoryResult:
        """Copy directory"""
        src = os.path.abspath(src)
        dst = os.path.abspath(dst)

        try:
            if not os.path.exists(src):
                return DirectoryResult(
                    success=False,
                    path=dst,
                    error=f"Source not found: {src}"
                )

            shutil.copytree(src, dst)

            return DirectoryResult(
                success=True,
                path=dst
            )
        except Exception as e:
            return DirectoryResult(
                success=False,
                path=dst,
                error=str(e)
            )

    def move(self, src: str, dst: str) -> DirectoryResult:
        """Move directory"""
        src = os.path.abspath(src)
        dst = os.path.abspath(dst)

        try:
            if not os.path.exists(src):
                return DirectoryResult(
                    success=False,
                    path=dst,
                    error=f"Source not found: {src}"
                )

            shutil.move(src, dst)

            return DirectoryResult(
                success=True,
                path=dst
            )
        except Exception as e:
            return DirectoryResult(
                success=False,
                path=dst,
                error=str(e)
            )

    def get_size(self, path: Optional[str] = None) -> int:
        """Get total size of directory"""
        path = os.path.abspath(path or self.base_path)
        total = 0

        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    total += os.path.getsize(os.path.join(root, file))
                except OSError:
                    pass

        return total

    def get_tree(
        self,
        path: Optional[str] = None,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Get directory tree structure"""
        path = os.path.abspath(path or self.base_path)

        def build_tree(p: str, depth: int) -> Dict[str, Any]:
            name = os.path.basename(p)
            node = {"name": name, "path": p}

            if os.path.isdir(p) and depth < max_depth:
                node["type"] = "directory"
                node["children"] = []
                try:
                    for item in sorted(os.listdir(p)):
                        if not item.startswith('.'):
                            child_path = os.path.join(p, item)
                            node["children"].append(build_tree(child_path, depth + 1))
                except PermissionError:
                    pass
            else:
                node["type"] = "file" if os.path.isfile(p) else "directory"
                node["size"] = os.path.getsize(p) if os.path.isfile(p) else 0

            return node

        return build_tree(path, 0)

    def exists(self, path: str) -> bool:
        """Check if directory exists"""
        return os.path.isdir(os.path.abspath(path))

    def is_empty(self, path: str) -> bool:
        """Check if directory is empty"""
        path = os.path.abspath(path)
        return os.path.isdir(path) and not os.listdir(path)

