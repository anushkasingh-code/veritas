"""
Pydantic schemas for web search results.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Normalized web search result item schema.
    """
    title: str = Field(..., description="Page or document title")
    url: str = Field(..., description="Source URL")
    content: str = Field(..., description="Main text snippet or raw document content")
    score: float = Field(default=0.0, description="Relevance score from search provider")
    published_date: Optional[str] = Field(default=None, description="Publication date string if available")
    domain: str = Field(..., description="Extracted domain name (e.g. reuters.com)")
    provider: str = Field(default="tavily", description="Search provider identifier")
