"""
NEXUS AI Agent - Plan Validator
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .task_planner import Plan, PlanStep
from .dependency_resolver import DependencyResolver

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """A validation issue"""
    severity: str  # error, warning, info
    message: str
    step_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of plan validation"""
    valid: bool
    issues: List[ValidationIssue]
    score: float  # 0-1 quality score


class PlanValidator:
    """
    Validates execution plans

    Checks:
    - Dependency validity
    - Step completeness
    - Resource availability
    - Logical consistency
    """

    def __init__(self):
        self._required_fields = ["name", "description"]
        self._available_tools: List[str] = []

    def set_available_tools(self, tools: List[str]) -> None:
        """Set available tools"""
        self._available_tools = tools

    def validate(self, plan: Plan) -> ValidationResult:
        """
        Validate a plan

        Args:
            plan: Plan to validate

        Returns:
            ValidationResult
        """
        issues: List[ValidationIssue] = []

        # Check basic structure
        issues.extend(self._validate_structure(plan))

        # Check dependencies
        issues.extend(self._validate_dependencies(plan))

        # Check tools
        issues.extend(self._validate_tools(plan))

        # Check completeness
        issues.extend(self._validate_completeness(plan))

        # Calculate validity and score
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        valid = len(errors) == 0
        score = max(0, 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05))

        return ValidationResult(
            valid=valid,
            issues=issues,
            score=score
        )

    def _validate_structure(self, plan: Plan) -> List[ValidationIssue]:
        """Validate plan structure"""
        issues = []

        if not plan.goal:
            issues.append(ValidationIssue(
                severity="error",
                message="Plan has no goal defined"
            ))

        if not plan.steps:
            issues.append(ValidationIssue(
                severity="error",
                message="Plan has no steps"
            ))

        for step in plan.steps:
            if not step.name:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Step {step.id} has no name",
                    step_id=step.id
                ))

            if not step.description:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"Step '{step.name}' has no description",
                    step_id=step.id
                ))

        return issues

    def _validate_dependencies(self, plan: Plan) -> List[ValidationIssue]:
        """Validate step dependencies"""
        issues = []
        step_ids = {s.id for s in plan.steps}
        step_names = {s.name.lower() for s in plan.steps}

        # Build dependency resolver
        resolver = DependencyResolver()
        for step in plan.steps:
            resolver.add_node(step.id, step.dependencies)

        # Check for cycles
        cycles = resolver.detect_cycles()
        for cycle in cycles:
            issues.append(ValidationIssue(
                severity="error",
                message=f"Circular dependency detected: {' -> '.join(cycle)}"
            ))

        # Check for missing dependencies
        for step in plan.steps:
            for dep in step.dependencies:
                if dep == "none" or dep == "":
                    continue
                if dep not in step_ids and dep.lower() not in step_names:
                    issues.append(ValidationIssue(
                        severity="error",
                        message=f"Step '{step.name}' has unknown dependency: {dep}",
                        step_id=step.id
                    ))

        return issues

    def _validate_tools(self, plan: Plan) -> List[ValidationIssue]:
        """Validate tool requirements"""
        issues = []

        if not self._available_tools:
            return issues  # Can't validate without tool list

        for step in plan.steps:
            for tool in step.tools_required:
                if tool and tool not in self._available_tools:
                    issues.append(ValidationIssue(
                        severity="warning",
                        message=f"Step '{step.name}' requires unavailable tool: {tool}",
                        step_id=step.id
                    ))

        return issues

    def _validate_completeness(self, plan: Plan) -> List[ValidationIssue]:
        """Validate plan completeness"""
        issues = []

        # Check for orphan steps (no connection to goal)
        if len(plan.steps) > 1:
            has_dependency = set()
            for step in plan.steps:
                for dep in step.dependencies:
                    has_dependency.add(dep)

            # First step should have no dependencies
            first_steps = [s for s in plan.steps if not s.dependencies or s.dependencies == ["none"]]
            if not first_steps:
                issues.append(ValidationIssue(
                    severity="warning",
                    message="No starting step found (all steps have dependencies)"
                ))

        # Check for reasonable number of steps
        if len(plan.steps) > 20:
            issues.append(ValidationIssue(
                severity="info",
                message=f"Plan has many steps ({len(plan.steps)}), consider breaking into sub-plans"
            ))

        return issues

    def suggest_improvements(self, plan: Plan) -> List[str]:
        """Suggest improvements for a plan"""
        suggestions = []
        validation = self.validate(plan)

        if not validation.valid:
            suggestions.append("Fix validation errors before executing")

        # Check step granularity
        for step in plan.steps:
            if len(step.description) > 500:
                suggestions.append(f"Consider breaking down step '{step.name}' into smaller steps")

        # Check for missing tools
        steps_without_tools = [s for s in plan.steps if not s.tools_required]
        if steps_without_tools:
            suggestions.append("Consider specifying tools for steps without tool assignments")

        return suggestions
