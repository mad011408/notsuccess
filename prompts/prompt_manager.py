"""
NEXUS AI Agent - Prompt Manager
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from config.logging_config import get_logger


logger = get_logger(__name__)


class PromptManager:
    """
    Manages prompt templates

    Features:
    - Template storage
    - Variable substitution
    - Prompt versioning
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        self._prompts: Dict[str, Dict[str, Any]] = {}
        self._prompts_dir = Path(prompts_dir) if prompts_dir else None
        self._load_default_prompts()

    def _load_default_prompts(self) -> None:
        """Load default system prompts"""
        self._prompts = {
            "default_system": {
                "template": "You are NEXUS, an advanced AI assistant. Be helpful, harmless, and honest.",
                "version": "1.0",
                "variables": []
            },
            "coder": {
                "template": """You are NEXUS, an expert software developer.
Write clean, efficient, well-documented code.
Follow best practices for {language}.
Current task: {task}""",
                "version": "1.0",
                "variables": ["language", "task"]
            },
            "researcher": {
                "template": """You are NEXUS, a thorough research assistant.
Research topic: {topic}
Be comprehensive, cite sources, and provide balanced analysis.""",
                "version": "1.0",
                "variables": ["topic"]
            },
            "analyst": {
                "template": """You are NEXUS, a data analyst expert.
Analyze the provided data carefully.
Focus on: {focus_area}
Provide actionable insights.""",
                "version": "1.0",
                "variables": ["focus_area"]
            }
        }

    def get(self, name: str, **variables) -> str:
        """
        Get a prompt with variables filled in

        Args:
            name: Prompt name
            **variables: Variables to substitute

        Returns:
            Formatted prompt string
        """
        if name not in self._prompts:
            raise ValueError(f"Unknown prompt: {name}")

        prompt_data = self._prompts[name]
        template = prompt_data["template"]

        # Substitute variables
        for var, value in variables.items():
            template = template.replace(f"{{{var}}}", str(value))

        return template

    def register(
        self,
        name: str,
        template: str,
        variables: Optional[List[str]] = None,
        version: str = "1.0"
    ) -> None:
        """Register a new prompt"""
        self._prompts[name] = {
            "template": template,
            "version": version,
            "variables": variables or []
        }

    def list_prompts(self) -> List[str]:
        """List available prompts"""
        return list(self._prompts.keys())

    def get_template(self, name: str) -> Dict[str, Any]:
        """Get raw template data"""
        return self._prompts.get(name, {})

    def save(self, path: Optional[str] = None) -> None:
        """Save prompts to file"""
        save_path = Path(path) if path else self._prompts_dir
        if save_path:
            save_path.mkdir(parents=True, exist_ok=True)
            with open(save_path / "prompts.json", "w") as f:
                json.dump(self._prompts, f, indent=2)

    def load(self, path: str) -> None:
        """Load prompts from file"""
        with open(path, "r") as f:
            loaded = json.load(f)
            self._prompts.update(loaded)


# Global prompt manager
prompt_manager = PromptManager()
