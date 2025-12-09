"""NEXUS AI Agent - Code Formatter"""

import subprocess
import tempfile
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class FormatterType(str, Enum):
    BLACK = "black"
    AUTOPEP8 = "autopep8"
    YAPF = "yapf"
    ISORT = "isort"
    PRETTIER = "prettier"
    ESLINT = "eslint"


@dataclass
class FormatResult:
    """Result of code formatting"""
    success: bool
    formatted_code: str = ""
    original_code: str = ""
    changes_made: bool = False
    error: Optional[str] = None


class CodeFormatter:
    """Format code using various formatters"""

    def __init__(self):
        self._formatters = {
            FormatterType.BLACK: self._format_black,
            FormatterType.AUTOPEP8: self._format_autopep8,
            FormatterType.YAPF: self._format_yapf,
            FormatterType.ISORT: self._format_isort,
            FormatterType.PRETTIER: self._format_prettier,
        }

    def format(
        self,
        code: str,
        formatter: FormatterType = FormatterType.BLACK,
        options: Optional[Dict] = None
    ) -> FormatResult:
        """
        Format code

        Args:
            code: Code to format
            formatter: Formatter to use
            options: Formatter options

        Returns:
            FormatResult
        """
        options = options or {}
        format_func = self._formatters.get(formatter)

        if not format_func:
            return FormatResult(
                success=False,
                original_code=code,
                error=f"Unknown formatter: {formatter}"
            )

        return format_func(code, options)

    def _format_black(self, code: str, options: Dict) -> FormatResult:
        """Format with Black"""
        try:
            import black

            line_length = options.get('line_length', 88)
            mode = black.Mode(line_length=line_length)

            formatted = black.format_str(code, mode=mode)

            return FormatResult(
                success=True,
                formatted_code=formatted,
                original_code=code,
                changes_made=formatted != code
            )
        except ImportError:
            return self._format_with_cli('black', code, ['-'])
        except Exception as e:
            return FormatResult(
                success=False,
                original_code=code,
                error=str(e)
            )

    def _format_autopep8(self, code: str, options: Dict) -> FormatResult:
        """Format with autopep8"""
        try:
            import autopep8

            formatted = autopep8.fix_code(code, options=options)

            return FormatResult(
                success=True,
                formatted_code=formatted,
                original_code=code,
                changes_made=formatted != code
            )
        except ImportError:
            return self._format_with_cli('autopep8', code, ['-'])
        except Exception as e:
            return FormatResult(
                success=False,
                original_code=code,
                error=str(e)
            )

    def _format_yapf(self, code: str, options: Dict) -> FormatResult:
        """Format with YAPF"""
        try:
            from yapf.yapflib.yapf_api import FormatCode

            formatted, changed = FormatCode(code)

            return FormatResult(
                success=True,
                formatted_code=formatted,
                original_code=code,
                changes_made=changed
            )
        except ImportError:
            return self._format_with_cli('yapf', code, [])
        except Exception as e:
            return FormatResult(
                success=False,
                original_code=code,
                error=str(e)
            )

    def _format_isort(self, code: str, options: Dict) -> FormatResult:
        """Format imports with isort"""
        try:
            import isort

            formatted = isort.code(code)

            return FormatResult(
                success=True,
                formatted_code=formatted,
                original_code=code,
                changes_made=formatted != code
            )
        except ImportError:
            return self._format_with_cli('isort', code, ['-'])
        except Exception as e:
            return FormatResult(
                success=False,
                original_code=code,
                error=str(e)
            )

    def _format_prettier(self, code: str, options: Dict) -> FormatResult:
        """Format with Prettier (JS/TS)"""
        parser = options.get('parser', 'babel')
        return self._format_with_cli(
            'prettier',
            code,
            ['--parser', parser, '--stdin-filepath', 'file.js']
        )

    def _format_with_cli(
        self,
        command: str,
        code: str,
        args: List[str]
    ) -> FormatResult:
        """Format using CLI tool"""
        try:
            process = subprocess.run(
                [command] + args,
                input=code.encode(),
                capture_output=True,
                timeout=30
            )

            if process.returncode == 0:
                formatted = process.stdout.decode('utf-8')
                return FormatResult(
                    success=True,
                    formatted_code=formatted,
                    original_code=code,
                    changes_made=formatted != code
                )
            else:
                return FormatResult(
                    success=False,
                    original_code=code,
                    error=process.stderr.decode('utf-8')
                )

        except FileNotFoundError:
            return FormatResult(
                success=False,
                original_code=code,
                error=f"{command} not found. Install it first."
            )
        except Exception as e:
            return FormatResult(
                success=False,
                original_code=code,
                error=str(e)
            )

    def format_file(
        self,
        file_path: str,
        formatter: Optional[FormatterType] = None,
        in_place: bool = False
    ) -> FormatResult:
        """Format a file"""
        # Auto-detect formatter based on extension
        if formatter is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.py':
                formatter = FormatterType.BLACK
            elif ext in ['.js', '.jsx', '.ts', '.tsx', '.json']:
                formatter = FormatterType.PRETTIER
            else:
                formatter = FormatterType.BLACK

        with open(file_path, 'r') as f:
            code = f.read()

        result = self.format(code, formatter)

        if result.success and in_place and result.changes_made:
            with open(file_path, 'w') as f:
                f.write(result.formatted_code)

        return result

    def check_format(
        self,
        code: str,
        formatter: FormatterType = FormatterType.BLACK
    ) -> bool:
        """Check if code is formatted correctly"""
        result = self.format(code, formatter)
        return result.success and not result.changes_made

