"""NEXUS AI Agent - Code Executor"""

import subprocess
import tempfile
import os
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    TYPESCRIPT = "typescript"


@dataclass
class ExecutionResult:
    """Result of code execution"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None


class CodeExecutor:
    """Execute code in various languages"""

    def __init__(self, timeout: int = 30, max_output_size: int = 10000):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self._language_commands = {
            Language.PYTHON: ["python", "-c"],
            Language.JAVASCRIPT: ["node", "-e"],
            Language.BASH: ["bash", "-c"],
            Language.TYPESCRIPT: ["npx", "ts-node", "-e"],
        }

    async def execute(
        self,
        code: str,
        language: Language = Language.PYTHON,
        env: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute code

        Args:
            code: Code to execute
            language: Programming language
            env: Environment variables

        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        try:
            command = self._language_commands.get(language)
            if not command:
                return ExecutionResult(
                    success=False,
                    error=f"Unsupported language: {language}"
                )

            # Execute in subprocess
            process = await asyncio.create_subprocess_exec(
                *command, code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **(env or {})}
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    success=False,
                    error="Execution timed out",
                    execution_time=self.timeout
                )

            execution_time = time.time() - start_time

            stdout_str = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
            stderr_str = stderr.decode('utf-8', errors='replace')[:self.max_output_size]

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode or 0,
                execution_time=execution_time
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def execute_file(
        self,
        file_path: str,
        language: Optional[Language] = None,
        args: Optional[List[str]] = None
    ) -> ExecutionResult:
        """Execute code from file"""
        import time
        start_time = time.time()

        # Detect language from extension
        if language is None:
            ext = os.path.splitext(file_path)[1].lower()
            language_map = {
                '.py': Language.PYTHON,
                '.js': Language.JAVASCRIPT,
                '.sh': Language.BASH,
                '.ts': Language.TYPESCRIPT,
            }
            language = language_map.get(ext, Language.PYTHON)

        command_map = {
            Language.PYTHON: ["python", file_path],
            Language.JAVASCRIPT: ["node", file_path],
            Language.BASH: ["bash", file_path],
            Language.TYPESCRIPT: ["npx", "ts-node", file_path],
        }

        command = command_map.get(language, ["python", file_path])
        if args:
            command.extend(args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    success=False,
                    error="Execution timed out"
                )

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout.decode('utf-8', errors='replace')[:self.max_output_size],
                stderr=stderr.decode('utf-8', errors='replace')[:self.max_output_size],
                return_code=process.returncode or 0,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def execute_with_file(
        self,
        code: str,
        language: Language = Language.PYTHON,
        filename: Optional[str] = None
    ) -> ExecutionResult:
        """Execute code by writing to temp file first"""
        ext_map = {
            Language.PYTHON: '.py',
            Language.JAVASCRIPT: '.js',
            Language.BASH: '.sh',
            Language.TYPESCRIPT: '.ts',
        }

        ext = ext_map.get(language, '.py')

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=ext,
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            return await self.execute_file(temp_path, language)
        finally:
            os.unlink(temp_path)

