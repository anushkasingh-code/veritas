"""
Fact Verification Agent module.
Evaluates atomic claims against retrieved web evidence context using batch structured LLM output.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.prompts.verifier_prompts import FACT_VERIFIER_SYSTEM_PROMPT
from app.graph.state import Claim, Source
from app.services.faiss_service import faiss_service
from app.llm.llm_factory import get_llm

logger = logging.getLogger(__name__)


class VerificationVerdictItem(BaseModel):
    """Structured Pydantic schema for single claim verification verdict in batch."""
    claim_id: str = Field(..., description="ID of the claim (e.g. 'claim_01')")
    verdict: str = Field(
        ...,
        description="Verification verdict: 'SUPPORTED', 'REFUTED', or 'INCONCLUSIVE'",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    reasoning: str = Field(
        ...,
        description="Concise explanation justifying the verdict based on evidence (max 200 chars)",
    )
    supporting_source_ids: List[str] = Field(
        default_factory=list,
        description="List of source IDs that corroborate the claim",
    )
    contradicting_source_ids: List[str] = Field(
        default_factory=list,
        description="List of source IDs that refute or contradict the claim",
    )


class BatchVerificationVerdicts(BaseModel):
    """Container schema for batch verification verdicts for all input claims."""
    verdicts: List[VerificationVerdictItem] = Field(
        ...,
        description="List of verification verdicts matching every input claim ID",
    )


async def verify_claim(
    claim: Claim,
    sources: List[Source],
    provider: Optional[str] = None,
) -> Claim:
    """Legacy single claim wrapper delegating to verify_claims_batch."""
    results = await verify_claims_batch(claims=[claim], sources=sources, job_id="", provider=provider)
    return results[0] if results else claim


async def verify_claims_batch(
    claims: List[Claim],
    sources: List[Source],
    job_id: str = "",
    provider: Optional[str] = None,
) -> List[Claim]:
    """
    Evaluates claims concurrently, with at most three LLM requests in flight, using
    top-3 FAISS similarity chunks and compressed evidence summaries.

    Args:
        claims: List of Claim domain objects to verify.
        sources: List of retrieved Source domain objects.
        job_id: Optional FAISS vector index identifier for similarity search.
        provider: Optional LLM provider override.

    Returns:
        List[Claim]: Updated Claim domain objects with verdicts, confidence, and reasoning.
    """
    if not claims:
        return []

    logger.info(f"Executing concurrent fact verification for {len(claims)} claims across {len(sources)} sources...")

    provider_clean = (provider or "").lower()
    base_llm = get_llm(provider=provider_clean, temperature=0.0)
    structured_llm = base_llm.with_structured_output(VerificationVerdictItem)
    semaphore = asyncio.Semaphore(3)

    async def verify_one(claim: Claim) -> Claim:
        claim_chunks: List[Dict[str, Any]] = []
        if job_id and faiss_service.has_index(job_id):
            try:
                claim_chunks = faiss_service.search_similar(index_id=job_id, query=claim.text, k=3)
            except Exception as exc:
                logger.warning("FAISS search failed for claim '%s': %s", claim.id, exc)

        if claim_chunks:
            claim_evidence_lines = [
                f"[{chunk.get('source_id', 'src_unknown')}] Title: {chunk.get('title', '')} | "
                f"Score: {round(float(chunk.get('score', 0.0)), 2)} | URL: {chunk.get('url', '')}\n"
                f"Summary: {chunk.get('snippet', '')[:400].strip()}"
                for chunk in claim_chunks
            ]
        else:
            claim_evidence_lines = [
                f"[{src.id}] Title: {src.title} | Score: {round(float(src.score or 0.0), 2)} | URL: {src.url}\n"
                f"Summary: {src.snippet[:400].strip()}"
                for src in sources[:4]
            ]
        claim_evidence = "\n\n".join(claim_evidence_lines) or "No web source evidence retrieved."
        prompt = (
            f"TARGET CLAIM TO VERIFY:\n"
            f"Claim ID: {claim.id}\nStatement: {claim.text}\nCategory: {claim.category}\n\n"
            f"COMPRESSED EVIDENCE CONTEXT:\n{claim_evidence}\n\n"
            "Cross-examine the evidence and return one structured verdict for this claim."
        )
        messages = [
            SystemMessage(content=FACT_VERIFIER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        async with semaphore:
            try:
                verdict: VerificationVerdictItem = await structured_llm.ainvoke(messages, max_tokens=2048)
                claim.verdict = verdict.verdict.upper()
                claim.confidence = round(verdict.confidence, 2)
                claim.reasoning = verdict.reasoning
                claim.supporting_sources = verdict.supporting_source_ids
                claim.contradicting_sources = verdict.contradicting_source_ids
            except Exception as exc:
                logger.error("Failed verification for claim '%s': %s", claim.id, exc, exc_info=True)
                claim.verdict = "INCONCLUSIVE"
                claim.confidence = 0.0
                claim.reasoning = f"Claim verification failed: {str(exc)}"
        return claim

    results = await asyncio.gather(*(verify_one(claim) for claim in claims))
    logger.info("Successfully processed %s claims concurrently.", len(results))
    return results
