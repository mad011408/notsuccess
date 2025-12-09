"""NEXUS AI Agent - File Search"""

import os
import re
import fnmatch
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SearchMatch:
    """Search match result"""
    path: str
    line_number: int = 0
    line_content: str = ""
    match_start: int = 0
    match_end: int = 0


@dataclass
class SearchResult:
    """Search result"""
    query: str
    matches: List[SearchMatch] = field(default_factory=list)
    files_searched: int = 0
    total_matches: int = 0


class FileSearch:
    """Search for files and content"""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getcwd()

    def find_files(
        self,
        pattern: str,
        path: Optional[str] = None,
        recursive: bool = True,
        include_hidden: bool = False,
        file_type: Optional[str] = None
    ) -> List[str]:
        """
        Find files matching pattern

        Args:
            pattern: Glob pattern (e.g., "*.py")
            path: Search path
            recursive: Search recursively
            include_hidden: Include hidden files
            file_type: Filter by type ('file', 'dir')

        Returns:
            List of matching paths
        """
        path = os.path.abspath(path or self.base_path)
        matches = []

        if recursive:
            for root, dirs, files in os.walk(path):
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]

                items = files if file_type == 'file' else (
                    dirs if file_type == 'dir' else files + dirs
                )

                for name in items:
                    if fnmatch.fnmatch(name, pattern):
                        matches.append(os.path.join(root, name))
        else:
            for name in os.listdir(path):
                if not include_hidden and name.startswith('.'):
                    continue

                full_path = os.path.join(path, name)
                if file_type == 'file' and not os.path.isfile(full_path):
                    continue
                if file_type == 'dir' and not os.path.isdir(full_path):
                    continue

                if fnmatch.fnmatch(name, pattern):
                    matches.append(full_path)

        return matches

    def grep(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: str = "*",
        recursive: bool = True,
        case_sensitive: bool = True,
        max_results: int = 1000,
        context_lines: int = 0
    ) -> SearchResult:
        """
        Search for pattern in files

        Args:
            pattern: Regex pattern to search
            path: Search path
            file_pattern: Filter files by pattern
            recursive: Search recursively
            case_sensitive: Case sensitive search
            max_results: Maximum results
            context_lines: Lines of context around match

        Returns:
            SearchResult
        """
        path = os.path.abspath(path or self.base_path)

        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        result = SearchResult(query=pattern)
        files = self.find_files(file_pattern, path, recursive, file_type='file')

        for file_path in files:
            result.files_searched += 1

            if result.total_matches >= max_results:
                break

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    for match in regex.finditer(line):
                        result.matches.append(SearchMatch(
                            path=file_path,
                            line_number=i,
                            line_content=line.rstrip(),
                            match_start=match.start(),
                            match_end=match.end()
                        ))
                        result.total_matches += 1

                        if result.total_matches >= max_results:
                            break

            except (IOError, OSError):
                continue

        return result

    def search_and_replace(
        self,
        pattern: str,
        replacement: str,
        path: Optional[str] = None,
        file_pattern: str = "*",
        recursive: bool = True,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Search and replace in files

        Args:
            pattern: Regex pattern to search
            replacement: Replacement string
            path: Search path
            file_pattern: Filter files
            recursive: Search recursively
            dry_run: Don't actually modify files

        Returns:
            Summary of changes
        """
        path = os.path.abspath(path or self.base_path)
        regex = re.compile(pattern)

        changes = {
            "files_modified": 0,
            "total_replacements": 0,
            "files": []
        }

        files = self.find_files(file_pattern, path, recursive, file_type='file')

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content, count = regex.subn(replacement, content)

                if count > 0:
                    changes["files_modified"] += 1
                    changes["total_replacements"] += count
                    changes["files"].append({
                        "path": file_path,
                        "replacements": count
                    })

                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)

            except (IOError, OSError):
                continue

        return changes

    def find_duplicates(
        self,
        path: Optional[str] = None,
        by_content: bool = True
    ) -> Dict[str, List[str]]:
        """Find duplicate files"""
        import hashlib
        path = os.path.abspath(path or self.base_path)

        if by_content:
            hashes: Dict[str, List[str]] = {}

            for root, _, files in os.walk(path):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        if file_hash not in hashes:
                            hashes[file_hash] = []
                        hashes[file_hash].append(file_path)
                    except (IOError, OSError):
                        continue

            return {k: v for k, v in hashes.items() if len(v) > 1}
        else:
            # By name
            names: Dict[str, List[str]] = {}
            for root, _, files in os.walk(path):
                for name in files:
                    if name not in names:
                        names[name] = []
                    names[name].append(os.path.join(root, name))

            return {k: v for k, v in names.items() if len(v) > 1}

    def find_large_files(
        self,
        path: Optional[str] = None,
        min_size: int = 10 * 1024 * 1024,  # 10MB
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Find large files"""
        path = os.path.abspath(path or self.base_path)
        files = []

        for root, _, filenames in os.walk(path):
            for name in filenames:
                file_path = os.path.join(root, name)
                try:
                    size = os.path.getsize(file_path)
                    if size >= min_size:
                        files.append({
                            "path": file_path,
                            "size": size,
                            "name": name
                        })
                except OSError:
                    continue

        files.sort(key=lambda x: x["size"], reverse=True)
        return files[:limit]

    def find_recent(
        self,
        path: Optional[str] = None,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Find recently modified files"""
        import time
        path = os.path.abspath(path or self.base_path)
        cutoff = time.time() - (days * 24 * 60 * 60)
        files = []

        for root, _, filenames in os.walk(path):
            for name in filenames:
                file_path = os.path.join(root, name)
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime >= cutoff:
                        files.append({
                            "path": file_path,
                            "modified": mtime,
                            "name": name
                        })
                except OSError:
                    continue

        files.sort(key=lambda x: x["modified"], reverse=True)
        return files[:limit]

