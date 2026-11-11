"""
LangGraph AgentState schema definition and Pydantic domain models for the Multi-Agent system.
"""

from typing import List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class Claim(BaseModel):
    """
    Structured model representing an atomic claim extracted from research query.
    """
    id: str = Field(..., description="Unique claim identifier (e.g. claim_01)")
    text: str = Field(..., description="The atomic claim statement text")
    category: str = Field(
        default="factual",
        description="Claim type category (e.g. factual, statistical, historical)",
    )
    verdict: Optional[str] = Field(
        default=None,
        description="Verification stance: SUPPORTED, REFUTED, or INCONCLUSIVE",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Verification confidence score between 0.0 and 1.0",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="LLM verification stance justification",
    )
    supporting_sources: List[str] = Field(
        default_factory=list,
        description="List of supporting source IDs",
    )
    contradicting_sources: List[str] = Field(
        default_factory=list,
        description="List of contradicting source IDs",
    )


class Source(BaseModel):
    """
    Structured model representing a web evidence source document snippet.
    """
    id: str = Field(..., description="Unique source identifier (e.g. src_01)")
    url: str = Field(..., description="Original web page URL")
    title: str = Field(..., description="Web document or page title")
    snippet: str = Field(..., description="Retrieved text content snippet")
    domain: Optional[str] = Field(default=None, description="Extracted web domain")
    score: Optional[float] = Field(default=None, description="Tavily relevance score")


class Contradiction(BaseModel):
    """
    Structured model representing a detected conflict between sources or claims.
    """
    claim_id: str = Field(..., description="ID of the related claim")
    source_a_id: str = Field(..., description="ID of the first conflicting source")
    source_b_id: str = Field(..., description="ID of the second conflicting source")
    conflict_description: str = Field(..., description="Detailed description of the discrepancy or contradiction")


class AgentState(TypedDict):
    """
    LangGraph shared state dictionary passed across multi-agent graph nodes.
    """
    job_id: str
    user_query: str
    model_provider: Optional[str]
    created_at: str
    completed_at: Optional[str]
    claims: List[Claim]
    sources: List[Source]
    faiss_index_id: Optional[str]
    contradictions: List[Contradiction]
    final_report: Optional[str]
    errors: List[str]
