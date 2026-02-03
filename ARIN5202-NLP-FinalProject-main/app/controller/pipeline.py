import json
import logging
import traceback
import time
from typing import Dict, Any

from app.controller.query_understanding import query_understanding
from app.controller.source_selection import source_selection
from app.controller.retrieval import retrieve_information
from app.controller.reranking import rerank_results
from app.controller.response_generation import generate_response
from app.constants import (
    LOG_PREFIX_PIPELINE,
    LOG_PIPELINE_UNDERSTANDING,
    LOG_PIPELINE_SOURCES,
    LOG_PIPELINE_RETRIEVAL_START,
    LOG_PIPELINE_RETRIEVAL_TOTAL,
    LOG_PIPELINE_RERANKING,
    LOG_PIPELINE_RERANKED,
    LOG_PIPELINE_GENERATING,
    LOG_PIPELINE_SUCCESS,
    LOG_PIPELINE_ERROR,
    ERROR_PIPELINE_PROCESSING
)

logger = logging.getLogger(__name__)

def run_search_pipeline(query: str) -> str:
    """
    Main search pipeline orchestrating all components:
    1. Query Understanding (LLM-based intent/domain classification)
    2. Source Selection (determine which APIs/sources to use)
    3. Information Retrieval (fetch from KB, Web, Domain APIs)
    4. Reranking (prioritize best results)
    5. Response Generation (synthesize final answer with HKGAI)
    
    Args:
        query: User's search query
        
    Returns:
        Generated response string
    """
    try:
        # Query Understanding
        understanding = query_understanding(query)
        understanding["query"] = query
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_UNDERSTANDING}: {json.dumps(understanding, indent=2, ensure_ascii=False)}")
        
        # Source Selection
        sources = source_selection(understanding)
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_SOURCES}: {json.dumps(sources, indent=2, ensure_ascii=False)}")
        
        # Information Retrieval
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_RETRIEVAL_START}")
        results = retrieve_information(query, understanding, sources)
        
        # Log retrieval results
        total_results = _count_total_results(results)
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_RETRIEVAL_TOTAL} {total_results} results total")
        
        # Reranking
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_RERANKING}")
        ranked_results = rerank_results(results, understanding)
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_RERANKED} {len(ranked_results)} results")

        # Response Generation
        logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_GENERATING}")
        response = generate_response(query, understanding, ranked_results)
        logger.info(f"{LOG_PREFIX_PIPELINE} Response generated")
        
        return response
        
    except Exception as e:
        logger.error(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_ERROR}: {str(e)}")
        traceback.print_exc()
        return f"{ERROR_PIPELINE_PROCESSING}: {str(e)}"


def _count_total_results(results: Dict[str, Any]) -> int:
    """
    Count total results from all sources
    
    Args:
        results: Dictionary containing results from different sources
        
    Returns:
        Total count of results
    """
    total = 0
    total += len(results.get("local_kb_results", []))
    total += len(results.get("web_results", []))
    
    domain_api_results = results.get("domain_api_results")
    if domain_api_results and "error" not in domain_api_results:
        total += 1
    
    return total