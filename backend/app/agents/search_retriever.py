"""
Search & Retrieval Agent module.
Fetches web search evidence for atomic claims via Tavily, embeds text snippets via SentenceTransformers,
and indexes vectors into a session FAISS index.
"""

import asyncio
import logging
from typing import Any, Dict, List, Set, Tuple

from app.graph.state import Claim, Source
from app.schemas.search import SearchResult
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.tavily_service import tavily_service

logger = logging.getLogger(__name__)


async def retrieve_and_index_evidence(
    job_id: str,
    claims: List[Claim],
    max_results_per_claim: int = 3,
) -> Tuple[List[Source], str]:
    """
    Retrieves web evidence for each claim, indexes text chunks into FAISS vector DB,
    and returns normalized Source items alongside the faiss_index_id.

    Args:
        job_id: Unique research analysis job identifier.
        claims: List of extracted Claim domain objects.
        max_results_per_claim: Number of Tavily search results per claim.

    Returns:
        Tuple[List[Source], str]: List of Source domain objects and the FAISS index_id string.
    """
    if not job_id or not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("job_id must be a non-empty string.")

    if not claims:
        logger.warning(f"No claims provided to search_retriever for job_id='{job_id}'. Returning empty sources.")
        return [], job_id

    clean_job_id = job_id.strip()
    logger.info(
        f"Executing search & retrieval for job_id='{clean_job_id}' across {len(claims)} claims "
        f"(max_results={max_results_per_claim} per claim)."
    )

    seen_urls: Set[str] = set()
    sources: List[Source] = []
    source_counter = 1

    for claim in claims:
        try:
            print(f"DEBUG: Executing Tavily search for claim '{claim.id}'...")
            search_results: List[SearchResult] = await asyncio.to_thread(
                tavily_service.search,
                query=claim.text,
                max_results=max_results_per_claim,
            )

            for item in search_results:
                if item.url in seen_urls:
                    continue

                seen_urls.add(item.url)
                source_id = f"src_{source_counter:02d}"
                source_counter += 1

                clean_snippet = item.content[:400].strip() if item.content else ""
                source_item = Source(
                    id=source_id,
                    url=item.url,
                    title=item.title,
                    snippet=clean_snippet,
                    domain=item.domain,
                    score=item.score,
                )
                sources.append(source_item)

        except Exception as e:
            logger.error(f"Search failed for claim '{claim.id}' ('{claim.text[:40]}...'): {e}", exc_info=True)
            print(f"DEBUG: Error in Tavily search for claim '{claim.id}': {e}")

    if not sources:
        logger.warning(f"No web sources retrieved for job_id='{clean_job_id}'. Skipping vector indexing.")
        return [], clean_job_id

    logger.info(f"Retrieved {len(sources)} unique evidence sources for job_id='{clean_job_id}'. Building FAISS index...")

    snippets = [src.snippet for src in sources]
    try:
        print(f"DEBUG: Generating embeddings for {len(snippets)} snippets...")
        embeddings = await asyncio.to_thread(embedding_service.embed_documents, snippets)
        vector_dim = embedding_service.dimension

        metadata_list: List[Dict[str, Any]] = [
            {
                "source_id": src.id,
                "url": src.url,
                "title": src.title,
                "domain": src.domain,
                "snippet": src.snippet,
            }
            for src in sources
        ]

        print(f"DEBUG: Creating FAISS index for job_id='{clean_job_id}'...")
        await asyncio.to_thread(faiss_service.create_index, index_id=clean_job_id, dimension=vector_dim)
        await asyncio.to_thread(
            faiss_service.add_vectors,
            index_id=clean_job_id,
            vectors=embeddings,
            metadata=metadata_list,
        )

        logger.info(
            f"Successfully populated FAISS index '{clean_job_id}' with {len(embeddings)} "
            f"vectors (dimension={vector_dim})."
        )
        return sources, clean_job_id

    except Exception as e:
        logger.error(f"Failed to generate embeddings or index vectors for job_id='{clean_job_id}': {e}", exc_info=True)
        print(f"DEBUG: Exception in embedding/FAISS indexing: {e}")
        return sources, clean_job_id
