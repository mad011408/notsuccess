"""NEXUS AI Agent - Code Analyzer"""

import ast
import re
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    line_number: int = 0
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str] = None
    line_number: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class CodeAnalysis:
    """Result of code analysis"""
    imports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    complexity: int = 0
    lines_of_code: int = 0
    comments: int = 0
    docstrings: int = 0
    issues: List[str] = field(default_factory=list)


class CodeAnalyzer:
    """Analyze Python code structure and quality"""

    def analyze(self, code: str) -> CodeAnalysis:
        """
        Analyze Python code

        Args:
            code: Python source code

        Returns:
            CodeAnalysis object
        """
        analysis = CodeAnalysis()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            analysis.issues.append(f"Syntax error: {e}")
            return analysis

        # Count lines
        lines = code.split('\n')
        analysis.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        analysis.comments = len([l for l in lines if l.strip().startswith('#')])

        # Analyze AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis.imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    analysis.imports.append(f"{module}.{alias.name}")

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                if not self._is_method(node, tree):
                    func_info = self._analyze_function(node)
                    analysis.functions.append(func_info)
                    if func_info.docstring:
                        analysis.docstrings += 1

            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                analysis.classes.append(class_info)
                if class_info.docstring:
                    analysis.docstrings += 1
                analysis.docstrings += len([m for m in class_info.methods if m.docstring])

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if self._is_global(node, tree):
                    analysis.global_variables.append(node.id)

        # Calculate complexity
        analysis.complexity = self._calculate_complexity(tree)

        # Check for issues
        analysis.issues.extend(self._check_issues(tree, code))

        return analysis

    def _analyze_function(self, node) -> FunctionInfo:
        """Analyze a function definition"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        returns = None
        if node.returns:
            returns = ast.unparse(node.returns)

        docstring = ast.get_docstring(node)

        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

        return FunctionInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=docstring,
            line_number=node.lineno,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef)
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition"""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_function(item))

        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)

        return ClassInfo(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node),
            line_number=node.lineno,
            decorators=decorators
        )

    def _is_method(self, node, tree) -> bool:
        """Check if function is a method"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False

    def _is_global(self, node, tree) -> bool:
        """Check if variable is global"""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for child in ast.walk(parent):
                    if child is node:
                        return False
        return True

    def _calculate_complexity(self, tree) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _check_issues(self, tree, code: str) -> List[str]:
        """Check for common issues"""
        issues = []

        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(f"Line {node.lineno}: Bare except clause")

            # Check for mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(f"Line {node.lineno}: Mutable default argument in {node.name}")

            # Check for unused variables (simple check)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id.startswith('_') and node.id != '_':
                    pass  # Intentionally unused

        # Check for long lines
        for i, line in enumerate(code.split('\n'), 1):
            if len(line) > 120:
                issues.append(f"Line {i}: Line too long ({len(line)} > 120)")

        return issues

    def get_summary(self, code: str) -> Dict[str, Any]:
        """Get a summary of code analysis"""
        analysis = self.analyze(code)
        return {
            "lines_of_code": analysis.lines_of_code,
            "num_functions": len(analysis.functions),
            "num_classes": len(analysis.classes),
            "num_imports": len(analysis.imports),
            "complexity": analysis.complexity,
            "num_issues": len(analysis.issues),
            "has_docstrings": analysis.docstrings > 0
        }

