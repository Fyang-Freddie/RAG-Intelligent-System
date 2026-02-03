import json
import logging
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi
from app.models.classifiers import ML_AVAILABLE
from app.constants import (
    BM25_WEIGHT_ORIGINAL,
    BM25_WEIGHT_BM25,
    DEFAULT_SCORE_LOCAL_KB,
    DEFAULT_SCORE_WEB,
    DEFAULT_SCORE_DOMAIN_API,
    RESULT_SOURCE_LOCAL_KB,
    RESULT_SOURCE_WEB,
    RESULT_SOURCE_DOMAIN_API,
    LOG_RERANKING_BM25_ERROR
)
from app.utils.profiler import timed_operation

logger = logging.getLogger(__name__)

def apply_bm25_reranking(query: str, results: List[Dict]) -> List[Dict]:
    """
    Apply BM25 reranking to results for better relevance scoring
    
    Args:
        query: User's search query
        results: List of result dictionaries with content and scores
        
    Returns:
        Results with updated scores combining original and BM25 scores
    """
    if not ML_AVAILABLE:
        return results
    
    try:
        # Extract text content from results
        texts = []
        for result in results:
            content = result.get("content", "")
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            texts.append(str(content))
        
        # Tokenize and compute BM25 scores
        tokenized_corpus = [text.lower().split() for text in texts]
        tokenized_query = query.lower().split()
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores
        max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
        normalized_scores = [score / max_score for score in bm25_scores]
        
        # Combine original and BM25 scores with weighted average
        for i, result in enumerate(results):
            original_score = result.get("score", DEFAULT_SCORE_LOCAL_KB)
            bm25_score = normalized_scores[i]
            result["score"] = BM25_WEIGHT_ORIGINAL * original_score + BM25_WEIGHT_BM25 * bm25_score
            result["bm25_score"] = float(bm25_score)
            
    except Exception as e:
        logger.error(f"{LOG_RERANKING_BM25_ERROR}: {e}")
    
    return results


@timed_operation("rerank_results")
def rerank_results(results: Dict[str, Any], understanding: Dict[str, Any]) -> List[Dict]:
    """
    Combine and rerank results from all sources
    
    Aggregates results from local KB, web search, and domain APIs,
    applies BM25 reranking if available, and sorts by relevance score.
    
    Args:
        results: Dictionary containing results from different sources
        understanding: Query understanding with intent, domain, entities
        
    Returns:
        Sorted list of all results by descending score
    """
    all_results = []
    
    # Aggregate local KB results
    for kb_result in results.get("local_kb_results", []):
        all_results.append({
            "content": kb_result.get("content", kb_result),
            "source": RESULT_SOURCE_LOCAL_KB,
            "score": kb_result.get("score", DEFAULT_SCORE_LOCAL_KB) if isinstance(kb_result, dict) else DEFAULT_SCORE_LOCAL_KB
        })
    
    # Aggregate web results
    for web_result in results.get("web_results", []):
        all_results.append({
            "content": web_result.get("content", web_result),
            "source": RESULT_SOURCE_WEB,
            "score": web_result.get("score", DEFAULT_SCORE_WEB) if isinstance(web_result, dict) else DEFAULT_SCORE_WEB
        })
    
    # Aggregate domain API results
    domain_results = results.get("domain_api_results", {})
    if domain_results:
        all_results.append({
            "content": domain_results,
            "source": RESULT_SOURCE_DOMAIN_API,
            "score": DEFAULT_SCORE_DOMAIN_API
        })
    
    # Apply BM25 reranking if available and multiple results exist
    if ML_AVAILABLE and len(all_results) > 1:
        query = understanding.get("query", "")
        all_results = apply_bm25_reranking(query, all_results)
    
    # Sort by score descending
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return all_results
