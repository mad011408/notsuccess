"""NEXUS AI Agent - Researcher Agent"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

from ..base_agent import BaseAgent, AgentOutput, AgentContext, AgentCapability
from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ResearchResult:
    """Research result"""
    query: str
    findings: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    summary: str = ""
    confidence: float = 0.0


class ResearcherAgent(BaseAgent):
    """
    Agent specialized in research tasks

    Capabilities:
    - Web search and information gathering
    - Document analysis
    - Source verification
    - Summary generation
    """

    def __init__(
        self,
        llm_client=None,
        search_tool=None,
        **kwargs
    ):
        super().__init__(
            name=kwargs.pop("name", "Researcher"),
            description="Specialized in research and information gathering",
            capabilities=[
                AgentCapability.WEB_SEARCH,
                AgentCapability.DOCUMENT_PROCESSING,
                AgentCapability.REASONING,
                AgentCapability.MEMORY,
            ],
            **kwargs
        )

        self.llm_client = llm_client
        self.search_tool = search_tool
        self._research_history: List[ResearchResult] = []

    async def run(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AgentOutput:
        """Execute research task"""
        self._running = True
        await self.emit("start", task)

        try:
            # Build research prompt
            research_prompt = self._build_research_prompt(task, context)

            # Perform research steps
            research_result = await self._conduct_research(task, context)

            # Generate summary
            summary = await self._generate_summary(research_result)

            # Store in history
            self._research_history.append(research_result)

            await self.emit("complete", summary)

            return AgentOutput(
                content=summary,
                agent_id=self.id,
                success=True,
                metadata={
                    "findings_count": len(research_result.findings),
                    "sources_count": len(research_result.sources),
                    "confidence": research_result.confidence
                }
            )

        except Exception as e:
            logger.error(f"Research error: {e}")
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
        """Execute research with streaming"""
        self._running = True

        try:
            yield f"Starting research on: {task}\n\n"

            # Search phase
            yield "## Searching for information...\n"
            if self.search_tool:
                results = await self.search_tool.search(task)
                for i, result in enumerate(results[:5], 1):
                    yield f"{i}. {result.get('title', 'Result')}\n"

            yield "\n## Analyzing findings...\n"

            # Analysis phase
            if self.llm_client:
                analysis_prompt = f"Analyze and summarize research findings for: {task}"
                async for chunk in self.llm_client.generate_stream(
                    messages=[{"role": "user", "content": analysis_prompt}],
                    model=self.model
                ):
                    yield chunk

            yield "\n\n## Research complete."

        except Exception as e:
            yield f"\nError during research: {e}"

        finally:
            self._running = False

    async def _conduct_research(
        self,
        query: str,
        context: Optional[AgentContext]
    ) -> ResearchResult:
        """Conduct research on query"""
        result = ResearchResult(query=query)

        # Search for information
        if self.search_tool:
            try:
                search_results = await self.search_tool.search(query)
                for item in search_results[:10]:
                    result.sources.append(item.get("url", ""))
                    result.findings.append(item.get("snippet", ""))
            except Exception as e:
                logger.warning(f"Search failed: {e}")

        # Analyze with LLM
        if self.llm_client and result.findings:
            analysis = await self.llm_client.generate(
                messages=[{
                    "role": "user",
                    "content": f"Analyze these findings about '{query}':\n" +
                              "\n".join(result.findings[:5])
                }],
                model=self.model
            )
            result.summary = analysis.content

        # Estimate confidence
        result.confidence = min(1.0, len(result.findings) * 0.1)

        return result

    async def _generate_summary(self, research: ResearchResult) -> str:
        """Generate research summary"""
        if research.summary:
            return research.summary

        if not research.findings:
            return f"No findings available for: {research.query}"

        # Generate summary from findings
        summary_parts = [
            f"# Research Summary: {research.query}",
            "",
            "## Key Findings:",
        ]

        for i, finding in enumerate(research.findings[:5], 1):
            summary_parts.append(f"{i}. {finding[:200]}...")

        if research.sources:
            summary_parts.extend([
                "",
                "## Sources:",
            ])
            for source in research.sources[:5]:
                if source:
                    summary_parts.append(f"- {source}")

        return "\n".join(summary_parts)

    def _build_research_prompt(
        self,
        task: str,
        context: Optional[AgentContext]
    ) -> str:
        """Build research prompt"""
        prompt = f"""You are a research agent. Your task is to:

1. Understand the research question
2. Identify key topics and subtopics
3. Search for relevant information
4. Analyze and synthesize findings
5. Provide a comprehensive summary

Research Task: {task}
"""
        if context and context.variables:
            prompt += f"\nAdditional Context: {context.variables}"

        return prompt

    def get_research_history(self) -> List[ResearchResult]:
        """Get research history"""
        return self._research_history.copy()

    def clear_history(self) -> None:
        """Clear research history"""
        self._research_history.clear()

