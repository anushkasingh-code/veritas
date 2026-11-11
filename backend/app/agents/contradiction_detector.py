"""
Contradiction Detector Agent module.
Cross-examines claims and sources to detect conflicting facts or data discrepancies using structured LLM output.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.prompts.contradiction_prompts import CONTRADICTION_DETECTOR_SYSTEM_PROMPT
from app.graph.state import Claim, Source, Contradiction
from app.llm.llm_factory import get_llm

logger = logging.getLogger(__name__)


class ContradictionItem(BaseModel):
    """Structured Pydantic schema for individual contradiction reports."""
    claim_id: str = Field(..., description="ID of the related claim")
    source_a_id: str = Field(..., description="ID of the first source in conflict")
    source_b_id: str = Field(..., description="ID of the second source in conflict")
    conflict_description: str = Field(..., description="Description of the discrepancy between sources")


class ContradictionReport(BaseModel):
    """Container schema for list of detected contradictions."""
    contradictions: List[ContradictionItem] = Field(
        default_factory=list,
        description="List of detected source-level contradictions",
    )


async def detect_contradictions(
    claims: List[Claim],
    sources: List[Source],
    provider: Optional[str] = None,
) -> List[Contradiction]:
    """
    Cross-examines retrieved sources against verified claims to spot contradictions across sources.

    Args:
        claims: Verified list of Claim objects.
        sources: List of retrieved Source objects.
        provider: Optional LLM provider override ('claude', 'openai', or 'gemini').

    Returns:
        List[Contradiction]: List of Contradiction domain objects.
    """
    if not claims or not sources:
        logger.info("Insufficient claims or sources for contradiction detection. Skipping.")
        return []

    logger.info(f"Cross-examining {len(sources)} sources across {len(claims)} claims for contradictions.")

    claims_text = "\n".join([f"[{c.id}] ({c.category}): {c.text} (Verdict: {c.verdict or 'UNVERIFIED'})" for c in claims])
    sources_text = "\n\n".join([
        f"[{s.id}] Title: {s.title} | Score: {round(float(s.score or 0.0), 2)} | URL: {s.url}\nSummary: {s.snippet[:400].strip()}"
        for s in sources[:6]
    ])

    try:
        provider_clean = (provider or "").lower()
        base_llm = get_llm(provider=provider_clean, temperature=0.0)
        structured_llm = base_llm.with_structured_output(ContradictionReport)

        prompt = (
            f"Claims under evaluation:\n{claims_text}\n\n"
            f"Retrieved Web Evidence Sources:\n{sources_text}\n\n"
            f"Cross-examine the evidence and report any conflicting facts or discrepancies."
        )

        messages = [
            SystemMessage(content=CONTRADICTION_DETECTOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        report: ContradictionReport = await structured_llm.ainvoke(messages)

        domain_contradictions: List[Contradiction] = []
        for item in report.contradictions:
            domain_contradictions.append(
                Contradiction(
                    claim_id=item.claim_id,
                    source_a_id=item.source_a_id,
                    source_b_id=item.source_b_id,
                    conflict_description=item.conflict_description,
                )
            )

        logger.info(f"Detected {len(domain_contradictions)} source-level contradictions.")
        return domain_contradictions

    except Exception as e:
        logger.error(f"Failed contradiction detection: {e}", exc_info=True)
        return []
