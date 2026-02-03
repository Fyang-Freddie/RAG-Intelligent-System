from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
import requests

from app.services.hkgenai import HKGAIClient
from app.constants import (
    INTENT_FACTUAL,
    DOMAIN_GENERAL,
    VALID_INTENTS,
    VALID_DOMAINS,
    ENTITY_KEY_LOCATIONS,
    ENTITY_KEY_ORGANIZATIONS,
    ENTITY_KEY_STOCK_SYMBOLS,
    ENTITY_KEY_DATES,
    ENTITY_KEY_PRODUCTS,
    ENTITY_KEY_GENERAL,
    DOMAIN_WEATHER,
    DOMAIN_TRANSPORTATION,
    DOMAIN_FINANCE,
    TEMPERATURE_LLM_CLASSIFICATION,
    MAX_TOKENS_LLM_CLASSIFICATION,
    LLM_CLASSIFICATION_SYSTEM_PROMPT,
    LLM_CLASSIFICATION_USER_PROMPT_TEMPLATE,
    MARKDOWN_JSON_START,
    MARKDOWN_CODE_START,
    CONTENT_PREVIEW_LENGTH_MEDIUM,
    LOG_PREFIX_LLM_CLASSIFICATION,
    LOG_PREFIX_QUERY_UNDERSTANDING,
    LOG_QU_API_ERROR,
    LOG_QU_EMPTY_RESPONSE,
    LOG_QU_INVALID_FORMAT,
    LOG_QU_INVALID_INTENT,
    LOG_QU_INVALID_DOMAIN,
    LOG_QU_CLASSIFICATION_SUCCESS,
    LOG_QU_ENTITIES,
    LOG_QU_JSON_ERROR,
    LOG_QU_RAW_CONTENT,
    LOG_QU_ERROR,
    LOG_QU_FAILED_DEFAULTS,
    LOG_QU_RESULT
)
from app.utils.profiler import timed_operation

logger = logging.getLogger(__name__)

def get_user_context() -> Dict[str, Any]:
    """
    Get current time and user location information.
    Uses IP-based geolocation as a simple default.
    
    Returns:
        Dictionary with current_time, location (city, country), timezone, and coordinates
    """
    context = {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": "Hong Kong",  # Default location
        "country": "Hong Kong",
        "timezone": "Asia/Hong_Kong",
        "latitude": 22.3193,
        "longitude": 114.1694
    }
    
    try:
        # Try to get more accurate location from IP geolocation
        response = requests.get("http://ip-api.com/json/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                context["location"] = data.get("city", "Hong Kong")
                context["country"] = data.get("country", "Hong Kong")
                context["timezone"] = data.get("timezone", "Asia/Hong_Kong")
                context["latitude"] = data.get("lat", 22.3193)
                context["longitude"] = data.get("lon", 114.1694)
                logger.info(f"Retrieved user location: {context['location']}, {context['country']}")
    except Exception as e:
        logger.debug(f"Could not retrieve location from IP, using default: {e}")
    
    return context

def classify_with_llm(query: str, user_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Use HKGAI LLM to classify query intent, domain, and extract domain-specific entities.
    Returns: {"intent": str, "domain": str, "needs_web": bool, "entities": dict}
    """
    try:
        client = HKGAIClient()
        
        system_prompt = LLM_CLASSIFICATION_SYSTEM_PROMPT
        
        # Add context information to user prompt if available
        context_str = ""
        if user_context:
            context_str = f"\n\nContext Information:\n- Current Time: {user_context.get('current_time')}\n- User Location: {user_context.get('location')}, {user_context.get('country')}\n- Timezone: {user_context.get('timezone')}\n\nUse this context when interpreting the query, especially for time-sensitive or location-specific queries.\n"
        
        user_prompt = LLM_CLASSIFICATION_USER_PROMPT_TEMPLATE.format(query=query) + context_str
        
        response = client.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=MAX_TOKENS_LLM_CLASSIFICATION,
            temperature=TEMPERATURE_LLM_CLASSIFICATION
        )
        
        if "error" in response:
            logger.error(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_API_ERROR}: {response['error']}")
            return None
        
        content = response.get("content", "").strip()
        if not content:
            logger.warning(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_EMPTY_RESPONSE}")
            return None
        
        # Parse JSON response - remove markdown code blocks if present
        if content.startswith(MARKDOWN_JSON_START):
            content = content.replace(MARKDOWN_JSON_START, "").replace(MARKDOWN_CODE_START, "").strip()
        elif content.startswith(MARKDOWN_CODE_START):
            content = content.replace(MARKDOWN_CODE_START, "").strip()
        
        result = json.loads(content)
        
        # Validate required fields
        if "intent" not in result or "domain" not in result:
            logger.warning(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_INVALID_FORMAT}: {result}")
            return None
        
        # Validate intent and domain values
        if result["intent"] not in VALID_INTENTS:
            logger.warning(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_INVALID_INTENT}: {result['intent']}")
            return None
        
        if result["domain"] not in VALID_DOMAINS:
            logger.warning(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_INVALID_DOMAIN}: {result['domain']}")
            return None
        
        # Set default values if not provided
        if "needs_web" not in result:
            result["needs_web"] = result["domain"] in [DOMAIN_WEATHER, DOMAIN_TRANSPORTATION, DOMAIN_FINANCE]
        if "entities" not in result:
            result["entities"] = _create_empty_entities()
        
        # Ensure entities is a dict with all expected keys
        entities = result.get("entities", {})
        if not isinstance(entities, dict):
            entities = {ENTITY_KEY_GENERAL: entities if isinstance(entities, list) else []}
        
        for key in [ENTITY_KEY_LOCATIONS, ENTITY_KEY_ORGANIZATIONS, ENTITY_KEY_STOCK_SYMBOLS,
                    ENTITY_KEY_DATES, ENTITY_KEY_PRODUCTS, ENTITY_KEY_GENERAL]:
            if key not in entities:
                entities[key] = []
        
        result["entities"] = entities
        
        logger.info(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_CLASSIFICATION_SUCCESS}: {result['intent']}, Domain: {result['domain']}, Needs Web: {result.get('needs_web', False)}")
        logger.debug(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_ENTITIES}: {result['entities']}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_JSON_ERROR}: {e}")
        logger.debug(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_RAW_CONTENT}: {content[:CONTENT_PREVIEW_LENGTH_MEDIUM]}")
        return None
    except Exception as e:
        logger.error(f"{LOG_PREFIX_LLM_CLASSIFICATION} {LOG_QU_ERROR}: {e}")
        return None
    
@timed_operation("query_understanding")
def query_understanding(query: str) -> Dict[str, Any]:
    """
    Understand query using HKGAI LLM for intent, domain, entity extraction, and web search decision.
    Supports both English and Traditional Chinese queries.
    Includes current time and location context.
    
    Args:
        query: User's search query
        
    Returns:
        Dictionary with intent, domain, needs_web, entities, and user_context
    """
    # Get current time and location context
    user_context = get_user_context()
    logger.info(f"{LOG_PREFIX_QUERY_UNDERSTANDING} User context: {user_context['current_time']}, {user_context['location']}")
    
    # Use LLM classification with entity extraction and context
    llm_result = classify_with_llm(query, user_context)
    
    if not llm_result:
        # If LLM fails, return default values with context
        logger.warning(f"{LOG_PREFIX_QUERY_UNDERSTANDING} {LOG_QU_FAILED_DEFAULTS}")
        return {
            "intent": INTENT_FACTUAL,
            "domain": DOMAIN_GENERAL,
            "needs_web": True,
            "entities": _create_empty_entities(),
            "user_context": user_context
        }
    
    intent = llm_result["intent"]
    domain = llm_result["domain"]
    needs_web = llm_result.get("needs_web", False)
    entities = llm_result.get("entities", {})
    
    logger.info(f"{LOG_PREFIX_QUERY_UNDERSTANDING} {LOG_QU_RESULT}={intent}, Domain={domain}, Needs Web={needs_web}")

    return {
        "intent": intent, 
        "domain": domain, 
        "needs_web": needs_web, 
        "entities": entities,
        "user_context": user_context
    }


def _create_empty_entities() -> Dict[str, List]:
    """
    Create empty entities dictionary with all expected keys
    
    Returns:
        Dictionary with empty lists for all entity types
    """
    return {
        ENTITY_KEY_LOCATIONS: [],
        ENTITY_KEY_ORGANIZATIONS: [],
        ENTITY_KEY_STOCK_SYMBOLS: [],
        ENTITY_KEY_DATES: [],
        ENTITY_KEY_PRODUCTS: [],
        ENTITY_KEY_GENERAL: []
    }
