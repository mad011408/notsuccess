"""NEXUS AI Agent - Coder Agent"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

from ..base_agent import BaseAgent, AgentOutput, AgentContext, AgentCapability
from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class CodeResult:
    """Code execution result"""
    code: str
    language: str
    output: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0


class CoderAgent(BaseAgent):
    """
    Agent specialized in coding tasks

    Capabilities:
    - Code generation
    - Code review
    - Bug fixing
    - Code execution
    - Documentation generation
    """

    def __init__(
        self,
        llm_client=None,
        code_executor=None,
        **kwargs
    ):
        super().__init__(
            name=kwargs.pop("name", "Coder"),
            description="Specialized in code generation and analysis",
            capabilities=[
                AgentCapability.CODE_EXECUTION,
                AgentCapability.FILE_OPERATIONS,
                AgentCapability.REASONING,
            ],
            **kwargs
        )

        self.llm_client = llm_client
        self.code_executor = code_executor
        self._code_history: List[CodeResult] = []

    async def run(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AgentOutput:
        """Execute coding task"""
        self._running = True
        await self.emit("start", task)

        try:
            # Determine task type
            task_type = self._classify_task(task)

            if task_type == "generate":
                result = await self._generate_code(task, context)
            elif task_type == "review":
                result = await self._review_code(task, context)
            elif task_type == "fix":
                result = await self._fix_code(task, context)
            elif task_type == "explain":
                result = await self._explain_code(task, context)
            else:
                result = await self._generate_code(task, context)

            await self.emit("complete", result)

            return AgentOutput(
                content=result,
                agent_id=self.id,
                success=True,
                metadata={"task_type": task_type}
            )

        except Exception as e:
            logger.error(f"Coder error: {e}")
            await self.emit("error", e)
            return AgentOutput(
                content="",
                agent_id=self.id,
                success=False,
                error=str(e)
            )

        finally:
            self._running = False

    async def run_stream(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AsyncGenerator[str, None]:
        """Execute coding task with streaming"""
        self._running = True

        try:
            prompt = self._build_coding_prompt(task, context)

            if self.llm_client:
                async for chunk in self.llm_client.generate_stream(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model
                ):
                    yield chunk
            else:
                yield f"Code generation request: {task}"

        except Exception as e:
            yield f"\nError: {e}"

        finally:
            self._running = False

    def _classify_task(self, task: str) -> str:
        """Classify the coding task"""
        task_lower = task.lower()

        if any(word in task_lower for word in ["review", "check", "analyze"]):
            return "review"
        elif any(word in task_lower for word in ["fix", "debug", "solve", "error"]):
            return "fix"
        elif any(word in task_lower for word in ["explain", "document", "describe"]):
            return "explain"
        else:
            return "generate"

    async def _generate_code(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Generate code for task"""
        prompt = f"""You are an expert programmer. Generate clean, well-documented code for the following task:

Task: {task}

Requirements:
- Write production-quality code
- Include comments and docstrings
- Follow best practices
- Handle edge cases

Provide the code:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3
            )
            return response.content

        return f"# Code generation for: {task}"

    async def _review_code(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Review code"""
        prompt = f"""You are an expert code reviewer. Review the following code:

{task}

Provide:
1. Summary of what the code does
2. Potential issues or bugs
3. Security concerns
4. Performance considerations
5. Suggestions for improvement

Review:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return response.content

        return "Code review not available"

    async def _fix_code(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Fix code issues"""
        prompt = f"""You are an expert debugger. Analyze and fix the following code issue:

{task}

Provide:
1. Explanation of the bug/issue
2. Fixed code
3. Explanation of the fix

Fix:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.2
            )
            return response.content

        return "Bug fix not available"

    async def _explain_code(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Explain code"""
        prompt = f"""You are a programming teacher. Explain the following code:

{task}

Provide:
1. High-level overview
2. Line-by-line explanation
3. Key concepts used
4. Example usage

Explanation:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return response.content

        return "Code explanation not available"

    def _build_coding_prompt(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Build coding prompt"""
        prompt = f"""You are an expert programmer assistant.

Task: {task}
"""
        if context and context.variables:
            prompt += f"\nContext: {context.variables}"

        return prompt

    async def execute_code(
        self,
        code: str,
        language: str = "python"
    ) -> CodeResult:
        """Execute code and return result"""
        import time
        start_time = time.time()

        result = CodeResult(code=code, language=language)

        if self.code_executor:
            try:
                exec_result = await self.code_executor.execute(code, language)
                result.output = exec_result.stdout
                result.error = exec_result.stderr if not exec_result.success else None
            except Exception as e:
                result.error = str(e)

        result.execution_time = time.time() - start_time
        self._code_history.append(result)

        return result

    def get_code_history(self) -> List[CodeResult]:
        """Get code execution history"""
        return self._code_history.copy()

