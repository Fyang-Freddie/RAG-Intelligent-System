from typing import Dict, Any
import logging

from app.constants import (
    DOMAIN_FINANCE,
    DOMAIN_WEATHER,
    DOMAIN_TRANSPORTATION,
    DOMAIN_GENERAL,
    INTENT_CONVERSATIONAL,
    SOURCE_DOMAIN_API,
    SOURCE_WEB_SEARCH,
    SOURCE_LOCAL_KB,
    LOG_PREFIX_SOURCE_SELECTION,
    LOG_SS_FINANCE_API,
    LOG_SS_WEATHER_API,
    LOG_SS_TRANSPORT_API,
    LOG_SS_WEB_GENERAL,
    LOG_SS_WEB_SUPPLEMENTARY,
    LOG_SS_KB_PRIMARY,
    LOG_SS_KB_SUPPLEMENTARY,
    LOG_SS_FINAL
)
from app.utils.profiler import timed_operation

logger = logging.getLogger(__name__)

@timed_operation("source_selection")
def source_selection(understanding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide which sources to use based on query understanding.
    
    Sources:
    - local_kb: Local knowledge base (always checked for relevant context)
    - domain_api: Domain-specific APIs (finance, weather, transportation)
    - web_search: Real-time web search (when needs_web=True or recent data needed)
    
    Returns:
        {
            "sources": List[str],           # List of sources to query
            "domain_handler": str or None,  # Specific domain handler to use
            "priority": List[str]           # Order of source priority for reranking
        }
    """
    sources = []
    priority = []
    domain_handler = None
    
    domain = understanding.get("domain", DOMAIN_GENERAL)
    needs_web = understanding.get("needs_web", False)
    intent = understanding.get("intent", INTENT_CONVERSATIONAL)
    
    # Domain-specific API handlers
    if domain == DOMAIN_FINANCE:
        domain_handler = DOMAIN_FINANCE
        sources.append(SOURCE_DOMAIN_API)
        priority.append(SOURCE_DOMAIN_API)
        logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_FINANCE_API}")
        
    elif domain == DOMAIN_WEATHER:
        domain_handler = DOMAIN_WEATHER
        sources.append(SOURCE_DOMAIN_API)
        priority.append(SOURCE_DOMAIN_API)
        logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_WEATHER_API}")
        
    elif domain == DOMAIN_TRANSPORTATION:
        domain_handler = DOMAIN_TRANSPORTATION
        sources.append(SOURCE_DOMAIN_API)
        priority.append(SOURCE_DOMAIN_API)
        logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_TRANSPORT_API}")
    
    # Add web search based on needs_web flag from LLM
    if needs_web:
        sources.append(SOURCE_WEB_SEARCH)
        if domain == DOMAIN_GENERAL:
            priority.insert(0, SOURCE_WEB_SEARCH)
            logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_WEB_GENERAL}")
        else:
            priority.append(SOURCE_WEB_SEARCH)
            logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_WEB_SUPPLEMENTARY}")
    
    # Always check local KB, priority depends on query type
    sources.append(SOURCE_LOCAL_KB)
    if intent == INTENT_CONVERSATIONAL or (domain == DOMAIN_GENERAL and not needs_web):
        priority.insert(0, SOURCE_LOCAL_KB)
        logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_KB_PRIMARY}")
    else:
        priority.append(SOURCE_LOCAL_KB)
        logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_KB_SUPPLEMENTARY}")
    
    # Ensure priority list contains all sources
    for source in sources:
        if source not in priority:
            priority.append(source)
    
    result = {
        "sources": sources,
        "domain_handler": domain_handler,
        "priority": priority
    }
    
    logger.info(f"{LOG_PREFIX_SOURCE_SELECTION} {LOG_SS_FINAL}={sources}, Handler={domain_handler}, Priority={priority}")
    return result
