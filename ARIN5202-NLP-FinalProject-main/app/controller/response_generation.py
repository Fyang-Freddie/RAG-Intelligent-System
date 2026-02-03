import json
import logging
from typing import Dict, List, Any, Optional

from app.services.hkgenai import HKGAIClient
from app.constants import (
    RESULT_SOURCE_DOMAIN_API,
    RESULT_SOURCE_WEB,
    MAX_TOKENS_RESPONSE_GENERATION,
    TEMPERATURE_RESPONSE_GENERATION,
    DEFAULT_MAX_SUPPORTING_WEB,
    DEFAULT_MAX_CONTEXT_RESULTS,
    CONTENT_PREVIEW_LENGTH_MEDIUM,
    DOMAIN_GENERAL,
    INTENT_CONVERSATIONAL,
    RESPONSE_GENERATION_SYSTEM_PROMPT_TEMPLATE,
    RESPONSE_GENERATION_USER_PROMPT_TEMPLATE,
    RESPONSE_CONTEXT_HEADER,
    RESPONSE_PRIMARY_SOURCE_HEADER,
    RESPONSE_SUPPORTING_WEB_HEADER,
    RESPONSE_SOURCE_HEADER_TEMPLATE,
    LOG_RESPONSE_ERROR,
    LOG_RESPONSE_FALLBACK
)
from app.utils.profiler import timed_operation

logger = logging.getLogger(__name__)

hkgai_client = HKGAIClient()


@timed_operation("generate_response")
def generate_response(query: str, understanding: Dict[str, Any], context: List[Dict]) -> str:
    """
    Generate final response using HKGAI with retrieved context
    
    Prioritizes domain API results when available, supplements with web
    results, and uses top results for general queries.
    
    Args:
        query: User's search query
        understanding: Query understanding with intent and domain
        context: List of ranked context results from all sources
        
    Returns:
        Generated response string
    """
    # Extract domain API result if present
    domain_api_result = _extract_domain_api_result(context)
    
    # Build context summary for LLM
    context_summary = _build_context_summary(context, domain_api_result)
    
    # Extract domain and intent
    domain = understanding.get("domain", DOMAIN_GENERAL)
    intent = understanding.get("intent", INTENT_CONVERSATIONAL)
    
    # Build prompts from templates
    system_prompt = RESPONSE_GENERATION_SYSTEM_PROMPT_TEMPLATE.format(
        intent=intent,
        domain=domain
    )
    
    user_prompt = RESPONSE_GENERATION_USER_PROMPT_TEMPLATE.format(
        query=query,
        context_summary=context_summary
    )
    
    # Call LLM to generate response
    result = hkgai_client.chat(
        system_prompt,
        user_prompt,
        max_tokens=MAX_TOKENS_RESPONSE_GENERATION,
        temperature=TEMPERATURE_RESPONSE_GENERATION
    )
    
    if "error" in result:
        logger.error(f"Response generation error: {result['error']}")
        return LOG_RESPONSE_ERROR
    
    return result.get("content", LOG_RESPONSE_FALLBACK)


def _extract_domain_api_result(context: List[Dict]) -> Optional[Dict]:
    """
    Extract domain API result from context if present
    
    Args:
        context: List of context results
        
    Returns:
        Domain API result dict or None
    """
    for ctx in context:
        if ctx.get("source") == RESULT_SOURCE_DOMAIN_API and isinstance(ctx.get("content"), dict):
            return ctx.get("content")
    return None


def _extract_web_results(context: List[Dict], max_results: int = DEFAULT_MAX_SUPPORTING_WEB) -> List[Dict]:
    """
    Extract web results from context
    
    Args:
        context: List of context results
        max_results: Maximum number of web results to return
        
    Returns:
        List of web result dictionaries
    """
    return [ctx for ctx in context if ctx.get("source") == RESULT_SOURCE_WEB][:max_results]


def _build_context_summary(context: List[Dict], domain_api_result: Optional[Dict]) -> str:
    """
    Build formatted context summary for LLM prompt
    
    Args:
        context: List of all context results
        domain_api_result: Domain API result if available
        
    Returns:
        Formatted context summary string
    """
    if not context:
        return "No specific context retrieved. Use your general knowledge to provide a helpful answer."
    
    context_summary = RESPONSE_CONTEXT_HEADER
    
    # Prioritize domain API results when available
    if domain_api_result:
        context_summary += RESPONSE_PRIMARY_SOURCE_HEADER
        context_summary += json.dumps(domain_api_result, indent=2, ensure_ascii=False) + "\n"
        
        # Add supporting web results
        web_results = _extract_web_results(context)
        if web_results:
            context_summary += RESPONSE_SUPPORTING_WEB_HEADER
            for i, ctx in enumerate(web_results, 1):
                content = ctx.get("content", "")
                if isinstance(content, str):
                    context_summary += f"{i}. {content[:CONTENT_PREVIEW_LENGTH_MEDIUM]}...\n"
    else:
        # Use top results for general queries
        for i, ctx in enumerate(context[:DEFAULT_MAX_CONTEXT_RESULTS], 1):
            source = ctx.get("source", "unknown")
            content = ctx.get("content", {})
            context_summary += RESPONSE_SOURCE_HEADER_TEMPLATE.format(index=i, source=source)
            context_summary += json.dumps(content, indent=2, ensure_ascii=False) + "\n"
    
    return context_summary
