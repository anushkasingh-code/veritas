"""
Claim Extractor Agent module.
Decomposes input research queries into atomic, verifiable claims using structured LLM output.
"""

from enum import Enum
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.prompts.extractor_prompts import CLAIM_EXTRACTOR_SYSTEM_PROMPT
from app.graph.state import Claim
from app.llm.llm_factory import get_llm

logger = logging.getLogger(__name__)


class ClaimCategory(str, Enum):
    """Constrained categories for extracted atomic claims."""
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    HISTORICAL = "historical"


class ExtractedClaimItem(BaseModel):
    """Structured Pydantic model for individual extracted claim from LLM."""
    text: str = Field(..., description="The atomic claim statement text")
    category: ClaimCategory = Field(
        default=ClaimCategory.FACTUAL,
        description="Claim type category: 'factual', 'statistical', or 'historical'",
    )


class ExtractedClaimsList(BaseModel):
    """Pydantic container model for list of extracted claims."""
    claims: List[ExtractedClaimItem] = Field(
        ..., description="List of 2 to 5 extracted atomic claims"
    )


async def extract_claims(query: str, provider: Optional[str] = None) -> List[Claim]:
    """
    Analyzes user query and extracts atomic claims using structured LLM invocation.

    Args:
        query: Research query string.
        provider: Optional LLM provider override ('claude', 'openai', or 'gemini').

    Returns:
        List[Claim]: List of Claim domain objects with deterministic IDs (claim_01, claim_02, ...).
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise ValueError("Input query must be a non-empty string.")

    provider_clean = (provider or "").lower()
    logger.info(f"Initiating claim extraction using provider='{provider_clean or 'default'}' for query length={len(query)}")

    try:
        base_llm = get_llm(provider=provider_clean, temperature=0.0)
        structured_llm = base_llm.with_structured_output(ExtractedClaimsList)

        messages = [
            SystemMessage(content=CLAIM_EXTRACTOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Extract verifiable atomic claims from this research topic:\n\n{query.strip()}"),
        ]

        result: ExtractedClaimsList = await structured_llm.ainvoke(messages)

        if not result or not result.claims:
            logger.error("LLM claim extraction returned an empty list of claims.")
            raise ValueError("Claim extraction failed: No atomic claims were extracted from the input query.")

        domain_claims: List[Claim] = []
        for idx, item in enumerate(result.claims, start=1):
            deterministic_id = f"claim_{idx:02d}"
            domain_claims.append(
                Claim(
                    id=deterministic_id,
                    text=item.text.strip(),
                    category=item.category.value if isinstance(item.category, Enum) else str(item.category),
                )
            )

        logger.info(f"Successfully extracted {len(domain_claims)} atomic claims (IDs: {[c.id for c in domain_claims]})")
        return domain_claims

    except Exception as e:
        logger.error(f"Failed to extract claims using provider='{provider_clean or 'default'}': {e}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Claim extraction agent failed: {str(e)}") from e
