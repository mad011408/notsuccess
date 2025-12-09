"""NEXUS AI Agent - Writer Agent"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

from ..base_agent import BaseAgent, AgentOutput, AgentContext, AgentCapability
from config.logging_config import get_logger


logger = get_logger(__name__)


class WritingStyle(str, Enum):
    """Writing styles"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    BUSINESS = "business"


class ContentType(str, Enum):
    """Content types"""
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    EMAIL = "email"
    REPORT = "report"
    STORY = "story"
    DOCUMENTATION = "documentation"
    MARKETING = "marketing"


@dataclass
class WritingResult:
    """Writing result"""
    content: str
    content_type: ContentType
    style: WritingStyle
    word_count: int = 0
    reading_time: float = 0.0


class WriterAgent(BaseAgent):
    """
    Agent specialized in writing tasks

    Capabilities:
    - Content generation
    - Editing and proofreading
    - Style adaptation
    - Translation assistance
    """

    def __init__(
        self,
        llm_client=None,
        default_style: WritingStyle = WritingStyle.FORMAL,
        **kwargs
    ):
        super().__init__(
            name=kwargs.pop("name", "Writer"),
            description="Specialized in content creation and editing",
            capabilities=[
                AgentCapability.REASONING,
                AgentCapability.MEMORY,
            ],
            **kwargs
        )

        self.llm_client = llm_client
        self.default_style = default_style
        self._writing_history: List[WritingResult] = []

    async def run(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AgentOutput:
        """Execute writing task"""
        self._running = True
        await self.emit("start", task)

        try:
            # Parse task parameters
            params = self._parse_task(task, context)

            # Generate content
            content = await self._generate_content(
                task=params["task"],
                content_type=params["content_type"],
                style=params["style"],
                context=context
            )

            # Create result
            result = WritingResult(
                content=content,
                content_type=params["content_type"],
                style=params["style"],
                word_count=len(content.split()),
                reading_time=len(content.split()) / 200  # ~200 wpm
            )

            self._writing_history.append(result)

            await self.emit("complete", content)

            return AgentOutput(
                content=content,
                agent_id=self.id,
                success=True,
                metadata={
                    "word_count": result.word_count,
                    "reading_time_minutes": round(result.reading_time, 1),
                    "style": result.style.value,
                    "content_type": result.content_type.value
                }
            )

        except Exception as e:
            logger.error(f"Writer error: {e}")
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
        """Execute writing task with streaming"""
        self._running = True

        try:
            params = self._parse_task(task, context)
            prompt = self._build_writing_prompt(
                params["task"],
                params["content_type"],
                params["style"]
            )

            if self.llm_client:
                async for chunk in self.llm_client.generate_stream(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model
                ):
                    yield chunk
            else:
                yield f"Writing content for: {task}"

        except Exception as e:
            yield f"\nError: {e}"

        finally:
            self._running = False

    def _parse_task(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> Dict[str, Any]:
        """Parse task parameters"""
        task_lower = task.lower()

        # Detect content type
        content_type = ContentType.ARTICLE
        for ct in ContentType:
            if ct.value.replace("_", " ") in task_lower:
                content_type = ct
                break

        # Detect style
        style = self.default_style
        for s in WritingStyle:
            if s.value in task_lower:
                style = s
                break

        # Override from context
        if context and context.variables:
            if "style" in context.variables:
                style = WritingStyle(context.variables["style"])
            if "content_type" in context.variables:
                content_type = ContentType(context.variables["content_type"])

        return {
            "task": task,
            "content_type": content_type,
            "style": style
        }

    async def _generate_content(
        self,
        task: str,
        content_type: ContentType,
        style: WritingStyle,
        context: Optional[AgentContext]
    ) -> str:
        """Generate content"""
        prompt = self._build_writing_prompt(task, content_type, style)

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7
            )
            return response.content

        return f"# Generated Content\n\nContent for: {task}"

    def _build_writing_prompt(
        self,
        task: str,
        content_type: ContentType,
        style: WritingStyle
    ) -> str:
        """Build writing prompt"""
        style_guidelines = {
            WritingStyle.FORMAL: "Use formal language, avoid contractions, maintain professional tone.",
            WritingStyle.CASUAL: "Use conversational tone, contractions are fine, be friendly.",
            WritingStyle.TECHNICAL: "Use precise terminology, include technical details, be accurate.",
            WritingStyle.CREATIVE: "Be imaginative, use vivid descriptions, engage emotions.",
            WritingStyle.ACADEMIC: "Cite sources, use scholarly tone, be objective and analytical.",
            WritingStyle.BUSINESS: "Be concise, focus on value, maintain professional tone.",
        }

        type_guidelines = {
            ContentType.ARTICLE: "Write a well-structured article with introduction, body, and conclusion.",
            ContentType.BLOG_POST: "Write an engaging blog post with a hook and clear sections.",
            ContentType.EMAIL: "Write a clear, concise email with appropriate greeting and closing.",
            ContentType.REPORT: "Write a formal report with executive summary and detailed sections.",
            ContentType.STORY: "Write a narrative with characters, setting, and plot.",
            ContentType.DOCUMENTATION: "Write clear documentation with examples and step-by-step instructions.",
            ContentType.MARKETING: "Write persuasive copy that highlights benefits and includes call-to-action.",
        }

        return f"""You are an expert writer specializing in {content_type.value} content.

Writing Task: {task}

Style Guidelines: {style_guidelines[style]}

Content Guidelines: {type_guidelines[content_type]}

Write the requested content:"""

    async def edit(
        self,
        content: str,
        instructions: str = "Improve clarity and flow"
    ) -> str:
        """Edit existing content"""
        prompt = f"""Edit the following content according to these instructions: {instructions}

Content:
{content}

Edited version:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return response.content

        return content

    async def summarize(self, content: str, max_words: int = 100) -> str:
        """Summarize content"""
        prompt = f"""Summarize the following content in approximately {max_words} words:

{content}

Summary:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return response.content

        return content[:500] + "..."

    async def expand(self, content: str, target_words: int = 500) -> str:
        """Expand content"""
        prompt = f"""Expand the following content to approximately {target_words} words while maintaining the original message:

{content}

Expanded version:"""

        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return response.content

        return content

    def get_writing_history(self) -> List[WritingResult]:
        """Get writing history"""
        return self._writing_history.copy()

