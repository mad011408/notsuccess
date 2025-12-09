"""NEXUS AI Agent - Python REPL"""

import sys
import io
import traceback
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from contextlib import redirect_stdout, redirect_stderr


@dataclass
class REPLResult:
    """Result of REPL execution"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    return_value: Any = None
    variables: Dict[str, Any] = field(default_factory=dict)


class PythonREPL:
    """Interactive Python REPL environment"""

    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode
        self._globals: Dict[str, Any] = {}
        self._locals: Dict[str, Any] = {}
        self._history: List[str] = []
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Setup initial environment"""
        # Add common imports
        self._globals['__builtins__'] = __builtins__

        # Add safe modules
        import math
        import json
        import datetime
        import random
        import re
        import collections
        import itertools
        import functools

        self._globals.update({
            'math': math,
            'json': json,
            'datetime': datetime,
            'random': random,
            're': re,
            'collections': collections,
            'itertools': itertools,
            'functools': functools,
        })

    def execute(self, code: str) -> REPLResult:
        """
        Execute Python code

        Args:
            code: Python code to execute

        Returns:
            REPLResult
        """
        self._history.append(code)

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Try to eval first (for expressions)
                try:
                    result = eval(code, self._globals, self._locals)
                    if result is not None:
                        print(repr(result))
                    return_value = result
                except SyntaxError:
                    # Fall back to exec for statements
                    exec(code, self._globals, self._locals)
                    return_value = None

            output = stdout_capture.getvalue()

            return REPLResult(
                success=True,
                output=output,
                return_value=return_value,
                variables=self._get_user_variables()
            )

        except Exception as e:
            error_msg = traceback.format_exc()
            return REPLResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=error_msg,
                variables=self._get_user_variables()
            )

    def execute_multi(self, code_blocks: List[str]) -> List[REPLResult]:
        """Execute multiple code blocks"""
        results = []
        for code in code_blocks:
            result = self.execute(code)
            results.append(result)
            if not result.success:
                break
        return results

    def _get_user_variables(self) -> Dict[str, Any]:
        """Get user-defined variables"""
        user_vars = {}
        for key, value in self._locals.items():
            if not key.startswith('_'):
                try:
                    # Only include serializable values
                    repr(value)
                    user_vars[key] = type(value).__name__
                except:
                    pass
        return user_vars

    def get_variable(self, name: str) -> Any:
        """Get a variable value"""
        return self._locals.get(name, self._globals.get(name))

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable"""
        self._locals[name] = value

    def get_history(self) -> List[str]:
        """Get execution history"""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear execution history"""
        self._history.clear()

    def reset(self) -> None:
        """Reset REPL environment"""
        self._locals.clear()
        self._history.clear()
        self._setup_environment()

    def add_import(self, module_name: str, alias: Optional[str] = None) -> REPLResult:
        """Safely add an import"""
        if self.safe_mode:
            allowed_modules = {
                'math', 'json', 'datetime', 'random', 're',
                'collections', 'itertools', 'functools', 'string',
                'decimal', 'fractions', 'statistics', 'typing'
            }
            if module_name not in allowed_modules:
                return REPLResult(
                    success=False,
                    error=f"Module '{module_name}' not allowed in safe mode"
                )

        import_stmt = f"import {module_name}"
        if alias:
            import_stmt += f" as {alias}"

        return self.execute(import_stmt)

    def run_function(
        self,
        func_name: str,
        *args,
        **kwargs
    ) -> REPLResult:
        """Run a function defined in the REPL"""
        func = self._locals.get(func_name) or self._globals.get(func_name)
        if func is None:
            return REPLResult(
                success=False,
                error=f"Function '{func_name}' not found"
            )

        if not callable(func):
            return REPLResult(
                success=False,
                error=f"'{func_name}' is not callable"
            )

        try:
            result = func(*args, **kwargs)
            return REPLResult(
                success=True,
                return_value=result,
                output=repr(result) if result is not None else ""
            )
        except Exception as e:
            return REPLResult(
                success=False,
                error=traceback.format_exc()
            )

    def get_completions(self, prefix: str) -> List[str]:
        """Get completions for prefix"""
        completions = []

        # Check locals and globals
        all_names = set(self._locals.keys()) | set(self._globals.keys())
        for name in all_names:
            if name.startswith(prefix) and not name.startswith('_'):
                completions.append(name)

        # Check builtins
        for name in dir(__builtins__):
            if name.startswith(prefix) and not name.startswith('_'):
                completions.append(name)

        return sorted(completions)

