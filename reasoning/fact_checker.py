"""
NEXUS AI Agent - Fact Checker
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from config.logging_config import get_logger


logger = get_logger(__name__)


class FactStatus(str, Enum):
    """Status of a fact check"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FALSE = "false"
    PARTIALLY_TRUE = "partially_true"
    UNKNOWN = "unknown"


@dataclass
class FactCheckResult:
    """Result of a fact check"""
    claim: str
    status: FactStatus
    confidence: float
    evidence: List[str]
    sources: List[str]
    explanation: str


class FactChecker:
    """
    Verifies facts and claims in reasoning

    Uses multiple sources to verify claims.
    """

    def __init__(self):
        self._verification_sources: List[Callable] = []

    def add_source(self, source: Callable) -> None:
        """Add a verification source"""
        self._verification_sources.append(source)

    async def check_fact(
        self,
        claim: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None
    ) -> FactCheckResult:
        """
        Check a single fact/claim

        Args:
            claim: The claim to verify
            context: Additional context
            llm_call: LLM function for verification

        Returns:
            FactCheckResult
        """
        evidence = []
        sources = []

        # Gather evidence from sources
        for source in self._verification_sources:
            try:
                result = await source(claim)
                if result:
                    evidence.append(result)
                    sources.append(source.__name__)
            except Exception as e:
                logger.error(f"Source error: {e}")

        # Use LLM for verification if available
        if llm_call:
            llm_verdict = await self._llm_verify(claim, evidence, llm_call)
            evidence.append(llm_verdict["reasoning"])

            return FactCheckResult(
                claim=claim,
                status=FactStatus(llm_verdict["status"]),
                confidence=llm_verdict["confidence"],
                evidence=evidence,
                sources=sources + ["llm_analysis"],
                explanation=llm_verdict["explanation"]
            )

        # Without LLM, use simple heuristics
        return self._heuristic_check(claim, evidence, sources)

    async def check_multiple(
        self,
        claims: List[str],
        llm_call: Optional[Callable] = None
    ) -> List[FactCheckResult]:
        """Check multiple claims"""
        results = []
        for claim in claims:
            result = await self.check_fact(claim, llm_call=llm_call)
            results.append(result)
        return results

    async def _llm_verify(
        self,
        claim: str,
        evidence: List[str],
        llm_call: Callable
    ) -> Dict[str, Any]:
        """Use LLM to verify claim"""
        evidence_str = "\n".join(evidence) if evidence else "No external evidence available."

        prompt = f"""Verify this claim:

Claim: {claim}

Available evidence:
{evidence_str}

Analyze the claim and provide:
1. Status: verified/unverified/false/partially_true/unknown
2. Confidence: 0-1
3. Explanation: Why you reached this conclusion

Format:
STATUS: [status]
CONFIDENCE: [0-1]
EXPLANATION: [explanation]"""

        response = await llm_call(prompt)
        return self._parse_llm_response(response)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM verification response"""
        result = {
            "status": "unknown",
            "confidence": 0.5,
            "explanation": response,
            "reasoning": response
        }

        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if line.upper().startswith("STATUS:"):
                status = line.split(":", 1)[1].strip().lower()
                if status in [s.value for s in FactStatus]:
                    result["status"] = status
            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.upper().startswith("EXPLANATION:"):
                result["explanation"] = line.split(":", 1)[1].strip()

        return result

    def _heuristic_check(
        self,
        claim: str,
        evidence: List[str],
        sources: List[str]
    ) -> FactCheckResult:
        """Simple heuristic-based fact checking"""
        if not evidence:
            return FactCheckResult(
                claim=claim,
                status=FactStatus.UNKNOWN,
                confidence=0.3,
                evidence=[],
                sources=[],
                explanation="No evidence available to verify this claim."
            )

        # If we have evidence, assume partially verified
        return FactCheckResult(
            claim=claim,
            status=FactStatus.UNVERIFIED,
            confidence=0.5,
            evidence=evidence,
            sources=sources,
            explanation="Evidence gathered but not conclusively verified."
        )

    def extract_claims(self, text: str) -> List[str]:
        """Extract verifiable claims from text"""
        # Simple extraction - could be enhanced
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                # Look for factual patterns
                fact_indicators = ["is", "are", "was", "were", "has", "have", "will"]
                if any(f" {ind} " in sentence.lower() for ind in fact_indicators):
                    claims.append(sentence)

        return claims
