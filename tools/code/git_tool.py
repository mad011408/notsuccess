"""NEXUS AI Agent - Git Tool"""

import subprocess
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class GitResult:
    """Result of git operation"""
    success: bool
    output: str = ""
    error: Optional[str] = None


@dataclass
class GitStatus:
    """Git repository status"""
    branch: str = ""
    staged: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0


@dataclass
class GitCommit:
    """Git commit information"""
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str


class GitTool:
    """Git operations tool"""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()

    def _run(self, args: List[str]) -> GitResult:
        """Run git command"""
        try:
            process = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if process.returncode == 0:
                return GitResult(success=True, output=process.stdout.strip())
            else:
                return GitResult(
                    success=False,
                    output=process.stdout.strip(),
                    error=process.stderr.strip()
                )

        except FileNotFoundError:
            return GitResult(success=False, error="Git not installed")
        except subprocess.TimeoutExpired:
            return GitResult(success=False, error="Git command timed out")
        except Exception as e:
            return GitResult(success=False, error=str(e))

    def init(self) -> GitResult:
        """Initialize git repository"""
        return self._run(['init'])

    def clone(self, url: str, path: Optional[str] = None) -> GitResult:
        """Clone repository"""
        args = ['clone', url]
        if path:
            args.append(path)
        return self._run(args)

    def status(self) -> GitStatus:
        """Get repository status"""
        status = GitStatus()

        # Get branch
        result = self._run(['branch', '--show-current'])
        if result.success:
            status.branch = result.output

        # Get status
        result = self._run(['status', '--porcelain'])
        if result.success:
            for line in result.output.split('\n'):
                if not line:
                    continue
                status_code = line[:2]
                file_path = line[3:]

                if status_code[0] in ['M', 'A', 'D', 'R']:
                    status.staged.append(file_path)
                if status_code[1] == 'M':
                    status.modified.append(file_path)
                if status_code == '??':
                    status.untracked.append(file_path)

        # Get ahead/behind
        result = self._run(['rev-list', '--left-right', '--count', 'HEAD...@{upstream}'])
        if result.success:
            parts = result.output.split()
            if len(parts) == 2:
                status.ahead = int(parts[0])
                status.behind = int(parts[1])

        return status

    def add(self, files: Optional[List[str]] = None) -> GitResult:
        """Stage files"""
        if files:
            return self._run(['add'] + files)
        return self._run(['add', '.'])

    def commit(self, message: str, amend: bool = False) -> GitResult:
        """Create commit"""
        args = ['commit', '-m', message]
        if amend:
            args.append('--amend')
        return self._run(args)

    def push(
        self,
        remote: str = 'origin',
        branch: Optional[str] = None,
        force: bool = False
    ) -> GitResult:
        """Push to remote"""
        args = ['push', remote]
        if branch:
            args.append(branch)
        if force:
            args.append('--force')
        return self._run(args)

    def pull(
        self,
        remote: str = 'origin',
        branch: Optional[str] = None,
        rebase: bool = False
    ) -> GitResult:
        """Pull from remote"""
        args = ['pull', remote]
        if branch:
            args.append(branch)
        if rebase:
            args.append('--rebase')
        return self._run(args)

    def fetch(self, remote: str = 'origin') -> GitResult:
        """Fetch from remote"""
        return self._run(['fetch', remote])

    def checkout(self, branch: str, create: bool = False) -> GitResult:
        """Checkout branch"""
        args = ['checkout']
        if create:
            args.append('-b')
        args.append(branch)
        return self._run(args)

    def branch(self, name: Optional[str] = None, delete: bool = False) -> GitResult:
        """Branch operations"""
        if name is None:
            return self._run(['branch', '-a'])
        if delete:
            return self._run(['branch', '-d', name])
        return self._run(['branch', name])

    def merge(self, branch: str, no_ff: bool = False) -> GitResult:
        """Merge branch"""
        args = ['merge', branch]
        if no_ff:
            args.append('--no-ff')
        return self._run(args)

    def rebase(self, branch: str) -> GitResult:
        """Rebase onto branch"""
        return self._run(['rebase', branch])

    def log(self, count: int = 10, oneline: bool = False) -> List[GitCommit]:
        """Get commit log"""
        format_str = '%H|%h|%an|%ae|%ai|%s'
        result = self._run(['log', f'-{count}', f'--format={format_str}'])

        commits = []
        if result.success:
            for line in result.output.split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 6:
                    commits.append(GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        email=parts[3],
                        date=parts[4],
                        message=parts[5]
                    ))
        return commits

    def diff(
        self,
        file: Optional[str] = None,
        staged: bool = False,
        commit: Optional[str] = None
    ) -> GitResult:
        """Get diff"""
        args = ['diff']
        if staged:
            args.append('--staged')
        if commit:
            args.append(commit)
        if file:
            args.extend(['--', file])
        return self._run(args)

    def stash(self, pop: bool = False, message: Optional[str] = None) -> GitResult:
        """Stash operations"""
        if pop:
            return self._run(['stash', 'pop'])
        args = ['stash']
        if message:
            args.extend(['-m', message])
        return self._run(args)

    def reset(
        self,
        commit: str = 'HEAD',
        mode: str = 'mixed'
    ) -> GitResult:
        """Reset to commit"""
        return self._run(['reset', f'--{mode}', commit])

    def show(self, commit: str = 'HEAD') -> GitResult:
        """Show commit"""
        return self._run(['show', commit])

    def tag(
        self,
        name: Optional[str] = None,
        message: Optional[str] = None,
        delete: bool = False
    ) -> GitResult:
        """Tag operations"""
        if name is None:
            return self._run(['tag'])
        if delete:
            return self._run(['tag', '-d', name])
        args = ['tag', name]
        if message:
            args.extend(['-m', message])
        return self._run(args)

    def remote(self, verbose: bool = False) -> GitResult:
        """List remotes"""
        args = ['remote']
        if verbose:
            args.append('-v')
        return self._run(args)

    def config(self, key: str, value: Optional[str] = None, global_: bool = False) -> GitResult:
        """Get or set config"""
        args = ['config']
        if global_:
            args.append('--global')
        args.append(key)
        if value:
            args.append(value)
        return self._run(args)

