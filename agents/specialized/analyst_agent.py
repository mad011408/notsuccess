"""NEXUS AI Agent - Analyst Agent"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

from ..base_agent import BaseAgent, AgentOutput, AgentContext, AgentCapability
from config.logging_config import get_logger


logger = get_logger(__name__)


class AnalysisType(str, Enum):
    """Types of analysis"""
    DATA = "data"
    STATISTICAL = "statistical"
    TREND = "trend"
    COMPARATIVE = "comparative"
    SENTIMENT = "sentiment"
    FINANCIAL = "financial"
    MARKET = "market"


@dataclass
class AnalysisResult:
    """Analysis result"""
    analysis_type: AnalysisType
    summary: str
    findings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0


class AnalystAgent(BaseAgent):
    """
    Agent specialized in data analysis

    Capabilities:
    - Data analysis and interpretation
    - Statistical analysis
    - Trend identification
    - Report generation
    """

    def __init__(
        self,
        llm_client=None,
        data_tools=None,
        **kwargs
    ):
        super().__init__(
            name=kwargs.pop("name", "Analyst"),
            description="Specialized in data analysis and insights",
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.REASONING,
                AgentCapability.DATABASE,
            ],
            **kwargs
        )

        self.llm_client = llm_client
        self.data_tools = data_tools or {}
        self._analysis_history: List[AnalysisResult] = []

    async def run(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AgentOutput:
        """Execute analysis task"""
        self._running = True
        await self.emit("start", task)

        try:
            # Determine analysis type
            analysis_type = self._determine_analysis_type(task)

            # Perform analysis
            result = await self._perform_analysis(task, analysis_type, context)

            # Store result
            self._analysis_history.append(result)

            # Format output
            output = self._format_analysis_output(result)

            await self.emit("complete", output)

            return AgentOutput(
                content=output,
                agent_id=self.id,
                success=True,
                metadata={
                    "analysis_type": analysis_type.value,
                    "findings_count": len(result.findings),
                    "confidence": result.confidence
                }
            )

        except Exception as e:
            logger.error(f"Analyst error: {e}")
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
        """Execute analysis with streaming"""
        self._running = True

        try:
            analysis_type = self._determine_analysis_type(task)
            yield f"## {analysis_type.value.title()} Analysis\n\n"

            prompt = self._build_analysis_prompt(task, analysis_type)

            if self.llm_client:
                async for chunk in self.llm_client.generate_stream(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model
                ):
                    yield chunk
            else:
                yield f"Analysis for: {task}"

        except Exception as e:
            yield f"\nError: {e}"

        finally:
            self._running = False

    def _determine_analysis_type(self, task: str) -> AnalysisType:
        """Determine the type of analysis needed"""
        task_lower = task.lower()

        type_keywords = {
            AnalysisType.STATISTICAL: ["statistical", "statistics", "correlation", "regression"],
            AnalysisType.TREND: ["trend", "pattern", "over time", "growth"],
            AnalysisType.COMPARATIVE: ["compare", "comparison", "versus", "vs"],
            AnalysisType.SENTIMENT: ["sentiment", "opinion", "feedback", "reviews"],
            AnalysisType.FINANCIAL: ["financial", "revenue", "profit", "cost", "budget"],
            AnalysisType.MARKET: ["market", "competitor", "industry", "segment"],
        }

        for analysis_type, keywords in type_keywords.items():
            if any(kw in task_lower for kw in keywords):
                return analysis_type

        return AnalysisType.DATA

    async def _perform_analysis(
        self,
        task: str,
        analysis_type: AnalysisType,
        context: Optional[AgentContext]
    ) -> AnalysisResult:
        """Perform the analysis"""
        result = AnalysisResult(analysis_type=analysis_type)

        # Build analysis prompt
        prompt = self._build_analysis_prompt(task, analysis_type)

        # Get LLM analysis
        if self.llm_client:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3
            )

            # Parse response into structured result
            result.summary = response.content
            result.confidence = 0.8

            # Extract findings (simplified)
            lines = response.content.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    if "recommend" in line.lower():
                        result.recommendations.append(line[2:])
                    else:
                        result.findings.append(line[2:])

        return result

    def _build_analysis_prompt(
        self,
        task: str,
        analysis_type: AnalysisType
    ) -> str:
        """Build analysis prompt"""
        type_instructions = {
            AnalysisType.DATA: "Analyze the data, identify patterns, and provide insights.",
            AnalysisType.STATISTICAL: "Perform statistical analysis including mean, median, standard deviation, and significance tests.",
            AnalysisType.TREND: "Identify trends over time, growth rates, and predict future patterns.",
            AnalysisType.COMPARATIVE: "Compare the subjects, highlight differences and similarities.",
            AnalysisType.SENTIMENT: "Analyze sentiment, identify positive/negative aspects, and summarize opinions.",
            AnalysisType.FINANCIAL: "Analyze financial metrics, profitability, and provide financial insights.",
            AnalysisType.MARKET: "Analyze market position, competition, and opportunities.",
        }

        return f"""You are an expert data analyst.

Analysis Task: {task}

Analysis Type: {analysis_type.value}

Instructions: {type_instructions[analysis_type]}

Provide your analysis in the following format:
1. Executive Summary
2. Key Findings (as bullet points)
3. Detailed Analysis
4. Recommendations (as bullet points)
5. Conclusion

Analysis:"""

    def _format_analysis_output(self, result: AnalysisResult) -> str:
        """Format analysis result for output"""
        output_parts = [
            f"# {result.analysis_type.value.title()} Analysis Report",
            "",
            "## Summary",
            result.summary,
            ""
        ]

        if result.findings:
            output_parts.extend([
                "## Key Findings",
                *[f"- {f}" for f in result.findings],
                ""
            ])

        if result.metrics:
            output_parts.extend([
                "## Metrics",
                *[f"- {k}: {v}" for k, v in result.metrics.items()],
                ""
            ])

        if result.recommendations:
            output_parts.extend([
                "## Recommendations",
                *[f"- {r}" for r in result.recommendations],
                ""
            ])

        output_parts.append(f"*Confidence: {result.confidence:.0%}*")

        return "\n".join(output_parts)

    async def analyze_data(
        self,
        data: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyze structured data"""
        if not data:
            return AnalysisResult(
                analysis_type=AnalysisType.DATA,
                summary="No data provided for analysis"
            )

        # Basic data analysis
        result = AnalysisResult(analysis_type=AnalysisType.DATA)

        # Calculate basic metrics
        result.metrics["total_records"] = len(data)

        if data and isinstance(data[0], dict):
            result.metrics["fields"] = list(data[0].keys())

        # Use LLM for deeper analysis
        data_sample = data[:10] if len(data) > 10 else data
        analysis_task = f"Analyze this data sample: {data_sample}"

        llm_result = await self._perform_analysis(
            analysis_task,
            AnalysisType.DATA,
            None
        )

        result.summary = llm_result.summary
        result.findings = llm_result.findings
        result.recommendations = llm_result.recommendations
        result.confidence = llm_result.confidence

        return result

    def get_analysis_history(self) -> List[AnalysisResult]:
        """Get analysis history"""
        return self._analysis_history.copy()

