"""
NEXUS AI Agent - Prompt Builder
"""

from typing import Optional, List, Dict, Any


class PromptBuilder:
    """
    Fluent API for building prompts

    Usage:
        prompt = (PromptBuilder()
            .add_system("You are helpful")
            .add_context("User prefers code examples")
            .add_instruction("Answer the question")
            .build())
    """

    def __init__(self):
        self._system: str = ""
        self._context: List[str] = []
        self._instructions: List[str] = []
        self._examples: List[Dict[str, str]] = []
        self._constraints: List[str] = []
        self._output_format: str = ""

    def add_system(self, content: str) -> "PromptBuilder":
        """Add system message"""
        self._system = content
        return self

    def add_context(self, content: str) -> "PromptBuilder":
        """Add context"""
        self._context.append(content)
        return self

    def add_instruction(self, instruction: str) -> "PromptBuilder":
        """Add instruction"""
        self._instructions.append(instruction)
        return self

    def add_example(self, input: str, output: str) -> "PromptBuilder":
        """Add few-shot example"""
        self._examples.append({"input": input, "output": output})
        return self

    def add_constraint(self, constraint: str) -> "PromptBuilder":
        """Add constraint"""
        self._constraints.append(constraint)
        return self

    def set_output_format(self, format: str) -> "PromptBuilder":
        """Set output format"""
        self._output_format = format
        return self

    def build(self) -> str:
        """Build the final prompt"""
        parts = []

        if self._system:
            parts.append(self._system)

        if self._context:
            parts.append("\n## Context\n" + "\n".join(self._context))

        if self._instructions:
            parts.append("\n## Instructions\n" + "\n".join(f"- {i}" for i in self._instructions))

        if self._examples:
            examples_str = "\n## Examples\n"
            for ex in self._examples:
                examples_str += f"\nInput: {ex['input']}\nOutput: {ex['output']}\n"
            parts.append(examples_str)

        if self._constraints:
            parts.append("\n## Constraints\n" + "\n".join(f"- {c}" for c in self._constraints))

        if self._output_format:
            parts.append(f"\n## Output Format\n{self._output_format}")

        return "\n".join(parts)

    def build_messages(self) -> List[Dict[str, str]]:
        """Build as message list"""
        messages = []

        if self._system:
            messages.append({"role": "system", "content": self._system})

        for ex in self._examples:
            messages.append({"role": "user", "content": ex["input"]})
            messages.append({"role": "assistant", "content": ex["output"]})

        content_parts = []
        if self._context:
            content_parts.append("Context:\n" + "\n".join(self._context))
        if self._instructions:
            content_parts.append("Instructions:\n" + "\n".join(f"- {i}" for i in self._instructions))

        if content_parts:
            messages.append({"role": "user", "content": "\n\n".join(content_parts)})

        return messages

    def reset(self) -> "PromptBuilder":
        """Reset builder"""
        self._system = ""
        self._context = []
        self._instructions = []
        self._examples = []
        self._constraints = []
        self._output_format = ""
        return self
