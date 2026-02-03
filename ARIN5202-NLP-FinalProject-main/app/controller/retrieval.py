import re
import logging
from typing import Dict, Any, List
import requests
import yfinance as yf

from app.models.classifiers import load_local_retriever
from app.services.hkgenai import HKGAIClient
from app.config import (
    OPENWEATHER_API_KEY,
    SERPAPI_KEY
)
from app.constants import (
    DEFAULT_TOP_K_LOCAL_KB,
    DEFAULT_MAX_WEB_RESULTS,
    DEFAULT_SCORE_WEB_RESULTS,
    API_TIMEOUT_SECONDS,
    RESULT_SOURCE_LOCAL_KB,
    RESULT_SOURCE_GOOGLE_SEARCH,
    RESULT_SOURCE_WEB,
    SOURCE_LOCAL_KB,
    SOURCE_WEB_SEARCH,
    SOURCE_DOMAIN_API,
    DOMAIN_FINANCE,
    DOMAIN_WEATHER,
    DOMAIN_TRANSPORTATION,
    ENTITY_KEY_LOCATIONS,
    ENTITY_KEY_ORGANIZATIONS,
    LOG_PREFIX_LOCAL_KB,
    LOG_PREFIX_WEB_SEARCH,
    LOG_PREFIX_WEATHER_API,
    LOG_PREFIX_FINANCE_API,
    LOG_PREFIX_TRANSPORT_API,
    LOG_PREFIX_RETRIEVAL,
    LOG_RETRIEVAL_KB_UNAVAILABLE,
    LOG_RETRIEVAL_KB_FOUND,
    LOG_RETRIEVAL_KB_ERROR,
    LOG_RETRIEVAL_WEB_NO_API_KEY,
    LOG_RETRIEVAL_WEB_NO_CX,
    LOG_RETRIEVAL_WEB_NO_RESULTS,
    LOG_RETRIEVAL_WEB_FOUND,
    LOG_RETRIEVAL_WEB_API_FAILED,
    LOG_RETRIEVAL_WEB_ERROR,
    LOG_RETRIEVAL_WEATHER_NO_KEY,
    LOG_RETRIEVAL_WEATHER_SUCCESS,
    LOG_RETRIEVAL_WEATHER_FAILED,
    LOG_RETRIEVAL_WEATHER_ERROR,
    LOG_RETRIEVAL_FINANCE_NO_ORGS,
    LOG_RETRIEVAL_FINANCE_MAPPED,
    LOG_RETRIEVAL_FINANCE_AS_IS,
    LOG_RETRIEVAL_FINANCE_SUCCESS,
    LOG_RETRIEVAL_FINANCE_NOT_FOUND,
    LOG_RETRIEVAL_FINANCE_FAILED,
    LOG_RETRIEVAL_FINANCE_ERROR,
    LOG_RETRIEVAL_TRANSPORT_NO_KEY
)
from app.utils.profiler import timed_operation

logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_cities_from_locations(locations: List[str]) -> List[str]:
    """
    Extract city names from location entities
    
    Handles Hong Kong locations (English and Chinese) and other major cities.
    
    Args:
        locations: List of location strings from entity extraction
        
    Returns:
        List of normalized city names
    """
    cities = []
    
    for entity in locations:
        # Hong Kong locations (both English and Chinese)
        if any(loc in entity for loc in ["香港", "Hong Kong", "中環", "Central", "尖沙咀", "Tsim Sha Tsui", 
                                          "銅鑼灣", "Causeway Bay", "旺角", "Mong Kok", "灣仔", "Wan Chai"]):
            if "Hong Kong" not in cities:
                cities.append("Hong Kong")
        # Other major cities - use entity as-is
        elif len(entity) > 2:
            cities.append(entity)
    
    return cities

def _log_retrieval_summary(results: Dict[str, Any]) -> None:
    """
    Log summary of retrieval results
    
    Args:
        results: Dictionary containing retrieval results from all sources
    """
    total = (len(results["local_kb_results"]) + 
             len(results["web_results"]) + 
             (1 if results["domain_api_results"] and "error" not in results["domain_api_results"] else 0))
    logger.info(f"{LOG_PREFIX_RETRIEVAL} Total results retrieved: {total}")
    logger.info(f"{LOG_PREFIX_RETRIEVAL}   - Local KB: {len(results['local_kb_results'])}")
    logger.info(f"{LOG_PREFIX_RETRIEVAL}   - Web: {len(results['web_results'])}")
    logger.info(f"{LOG_PREFIX_RETRIEVAL}   - Domain API: {'✓' if results['domain_api_results'] and 'error' not in results['domain_api_results'] else '✗'}")


# ============================================================================
# LOCAL KNOWLEDGE BASE (FAISS VECTOR SEARCH)
# ============================================================================

@timed_operation("get_hkgai_answer")
def get_hkgai_answer(query: str) -> Dict[str, Any]:
    """
    Get HKGAI's independent answer to a query
    
    Args:
        query: User's search query
        
    Returns:
        Dictionary with HKGAI's answer formatted as a result, or empty dict on error
    """
    try:
        client = HKGAIClient()
        
        system_prompt = "You are a helpful assistant. Answer the user's question directly and concisely."
        user_prompt = query
        
        logger.info(f"{LOG_PREFIX_LOCAL_KB} Querying HKGAI for independent answer...")
        hkgai_response = client.chat(system_prompt, user_prompt, max_tokens=300, temperature=0.7)
        
        if "content" in hkgai_response and hkgai_response["content"]:
            hkgai_result = {
                "content": hkgai_response["content"],
                "score": 1.0,
                "source": "hkgai_direct",
                "rank": 0
            }
            logger.info(f"{LOG_PREFIX_LOCAL_KB} HKGAI direct answer retrieved")
            return hkgai_result
        else:
            logger.warning(f"{LOG_PREFIX_LOCAL_KB} HKGAI returned empty response")
            return {}
    except Exception as e:
        logger.error(f"{LOG_PREFIX_LOCAL_KB} HKGAI query error: {e}")
        return {}


@timed_operation("retrieve_from_local_kb")
def retrieve_from_local_kb(query: str, top_k: int = DEFAULT_TOP_K_LOCAL_KB) -> List[Dict]:
    """
    Retrieve information from local FAISS knowledge base using semantic search.
    
    Args:
        query: User's search query
        understanding: Query understanding dict (reserved for future use)
        top_k: Number of top results to return
        
    Returns:
        List of result dictionaries with content, score, source, and rank
    """
    model, index, documents = load_local_retriever()
    
    # If loading failed, return empty results
    if model is None or index is None or documents is None:
        logger.warning(f"{LOG_PREFIX_LOCAL_KB} {LOG_RETRIEVAL_KB_UNAVAILABLE}")
        return []
    
    try:
        # Encode query
        q_emb = model.encode([query], normalize_embeddings=True)
        
        # Search FAISS index
        scores, ids = index.search(q_emb, top_k)
        
        # Format results with similarity threshold filtering
        # FAISS cosine similarity ranges from 0 (dissimilar) to 1 (identical)
        # Filter out results with similarity < 0.3 (too irrelevant)
        MIN_SIMILARITY_THRESHOLD = 0.3
        results = []
        for i, idx in enumerate(ids[0]):
            similarity_score = float(scores[0][i])
            if similarity_score < MIN_SIMILARITY_THRESHOLD:
                logger.debug(f"{LOG_PREFIX_LOCAL_KB} Filtered result {i+1} (similarity: {similarity_score:.3f} < {MIN_SIMILARITY_THRESHOLD})")
                continue
            doc = documents[idx]
            result = {
                "content": doc["content"],
                "score": float(scores[0][i]),
                "source": RESULT_SOURCE_LOCAL_KB,
                "rank": i + 1
            }
            results.append(result)
        
        logger.info(f"{LOG_PREFIX_LOCAL_KB} {LOG_RETRIEVAL_KB_FOUND} {len(results)} results for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.error(f"{LOG_PREFIX_LOCAL_KB} {LOG_RETRIEVAL_KB_ERROR}: {e}")
        return []

# ========================================
# Web Search Functions (SerpAPI)
# ========================================

def _refine_search_query(original_query: str, user_context: Dict[str, Any] = None) -> str:
    """
    Use HKGAI to refine and optimize search query for better search results
    Incorporates user context (location, time) for better refinement
    
    Args:
        original_query: Original user query
        user_context: User context from query understanding (location, time, timezone)
        
    Returns:
        Refined search query optimized for search engines
    """
    try:
        client = HKGAIClient()
        
        system_prompt = """You are a search query optimization expert. Your task is to refine user queries into optimal search engine queries.

Rules:
1. Extract the core information need
2. Remove conversational elements (please, can you, I want to know, etc.)
3. Use specific keywords and proper nouns
4. Keep it concise (3-10 words ideal)
5. Maintain the original language if not English
6. For location queries, include specific place names
7. For time-sensitive queries, keep temporal indicators
8. Use user context (location, time) to enhance the query when relevant
9. Return ONLY the refined query, nothing else

Examples:
- "Can you tell me about the weather in Hong Kong?" → "Hong Kong weather"
- "What's the current stock price of Apple?" → "Apple stock price AAPL"
- "香港去中環怎麼去" → "香港 中環 交通路線"
- "I want to know if it will rain tomorrow in Tokyo" → "Tokyo weather forecast rain"
- "What's the weather like here?" (user in New York) → "New York weather"
"""
        
        # Build user prompt with context
        context_info = ""
        if user_context and isinstance(user_context, dict):
            location = user_context.get("location")
            country = user_context.get("country")
            current_time = user_context.get("current_time")
            if location:
                location_str = f"{location}, {country}" if country else location
                context_info += f"\nUser's location: {location_str}"
            if current_time:
                context_info += f"\nCurrent time: {current_time}"
        
        user_prompt = f"Refine this search query: {original_query}{context_info}"
        
        response = client.chat(system_prompt, user_prompt, max_tokens=50, temperature=0.3)
        
        if "content" in response and response["content"]:
            refined_query = response["content"].strip()
            logger.info(f"{LOG_PREFIX_WEB_SEARCH} Query refined: '{original_query}' → '{refined_query}'")
            return refined_query
        else:
            logger.warning(f"{LOG_PREFIX_WEB_SEARCH} HKGAI refinement returned empty, using original query")
            return original_query
    except Exception as e:
        logger.warning(f"{LOG_PREFIX_WEB_SEARCH} Query refinement failed: {e}, using original query")
        return original_query

def serpapi_search(query: str, max_results: int = DEFAULT_MAX_WEB_RESULTS, user_context: Dict[str, Any] = None) -> List[Dict]:
    """
    Perform search using SerpAPI with rate limit handling
    Automatically refines query using HKGAI before searching
    
    Args:
        query: Search query string (will be refined before searching)
        max_results: Maximum number of results to return
        user_context: User context from query understanding (location, time)
        
    Returns:
        List of search results with title, link, snippet, and source
    """
    if not SERPAPI_KEY:
        logger.warning(f"{LOG_PREFIX_WEB_SEARCH} {LOG_RETRIEVAL_WEB_NO_API_KEY}")
        return []
    
    # Refine query with HKGAI before searching (using user context)
    refined_query = _refine_search_query(query, user_context)
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": refined_query,
            "api_key": SERPAPI_KEY,
            "num": max_results,
            "engine": "google"  # Use Google search engine
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            data = response.json()
            organic_results = data.get("organic_results", [])
            
            if not organic_results:
                logger.info(f"{LOG_PREFIX_WEB_SEARCH} {LOG_RETRIEVAL_WEB_NO_RESULTS}: {refined_query}")
                return []
            
            results = []
            for item in organic_results[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "serpapi",
                    "original_query": query,
                    "refined_query": refined_query
                })
            
            logger.info(f"{LOG_PREFIX_WEB_SEARCH} {LOG_RETRIEVAL_WEB_FOUND} {len(results)} results for: {refined_query}")
            return results
        
        else:
            logger.error(f"{LOG_PREFIX_WEB_SEARCH} {LOG_RETRIEVAL_WEB_API_FAILED} {response.status_code}")
            if response.status_code == 403:
                logger.error(f"{LOG_PREFIX_WEB_SEARCH} 403 Forbidden - Check SerpAPI key validity")
            return []
            
    except Exception as e:
        logger.error(f"{LOG_PREFIX_WEB_SEARCH} {LOG_RETRIEVAL_WEB_ERROR}: {e}")
        return []

@timed_operation("retrieve_from_web")
def retrieve_from_web(query: str, user_context: Dict[str, Any] = None) -> List[Dict]:
    """
    Retrieve information from web search using SerpAPI
    
    Args:
        query: Search query string
        user_context: User context from query understanding (location, time)
        
    Returns:
        Formatted list of web results with content, title, url, source, and score
    """
    results = serpapi_search(query, max_results=DEFAULT_MAX_WEB_RESULTS, user_context=user_context)
    
    # Format results for pipeline
    formatted_results = []
    for result in results:
        formatted_results.append({
            "content": result.get("snippet", ""),
            "title": result.get("title", ""),
            "url": result.get("link", ""),
            "source": RESULT_SOURCE_WEB,
            "score": DEFAULT_SCORE_WEB_RESULTS
        })
    
    return formatted_results

# ========================================
# Domain-Specific API Functions
# ========================================

def _get_hk_aqhi() -> Dict[str, Any]:
    """
    Get Hong Kong Air Quality Health Index (AQHI) data from official HK Gov API
    AQHI scale: 1-10+ (Low, Moderate, High, Very High, Serious)
    """
    try:
        aqhi_url = "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_D_e.xml"
        response = requests.get(aqhi_url, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract AQHI data from XML
            aqhi_data = {}
            for region in root.findall('.//RegionalAQHI'):
                region_name = region.find('RegionName').text if region.find('RegionName') is not None else None
                current_aqhi = region.find('AQHI').text if region.find('AQHI') is not None else None
                health_risk = region.find('HealthRisk').text if region.find('HealthRisk') is not None else None
                
                if region_name and current_aqhi:
                    aqhi_data[region_name] = {
                        "aqhi": int(current_aqhi) if current_aqhi.isdigit() else current_aqhi,
                        "health_risk": health_risk
                    }
            
            # Get overall/general AQHI
            general = aqhi_data.get("General", {})
            if general:
                return {
                    "source": "Hong Kong EPD",
                    "aqhi": general.get("aqhi"),
                    "health_risk": general.get("health_risk"),
                    "regional_data": aqhi_data,
                    "scale": "1-10+ (Low: 1-3, Moderate: 4-6, High: 7, Very High: 8-10, Serious: 10+)"
                }
    except Exception as e:
        logger.debug(f"Error fetching HK AQHI: {e}")
    return None

def _get_hko_forecast() -> Dict[str, Any]:
    """
    Get Hong Kong Observatory local weather forecast
    Includes 9-day forecast with temperature, humidity, and weather conditions
    """
    try:
        # HKO 9-day forecast API
        forecast_url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"
        response = requests.get(forecast_url, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            
            # Extract general situation
            general_situation = data.get("generalSituation", "")
            
            # Extract forecast periods
            forecast_periods = []
            for period in data.get("weatherForecast", [])[:9]:
                forecast_periods.append({
                    "date": period.get("forecastDate"),
                    "week": period.get("week"),
                    "max_temp": period.get("forecastMaxtemp", {}).get("value"),
                    "min_temp": period.get("forecastMintemp", {}).get("value"),
                    "max_rh": period.get("forecastMaxrh", {}).get("value"),
                    "min_rh": period.get("forecastMinrh", {}).get("value"),
                    "weather": period.get("forecastWeather"),
                    "wind": period.get("forecastWind"),
                    "icon": period.get("ForecastIcon")
                })
            
            return {
                "source": "Hong Kong Observatory",
                "general_situation": general_situation,
                "forecast_periods": forecast_periods,
                "update_time": data.get("updateTime")
            }
    except Exception as e:
        logger.debug(f"Error fetching HKO forecast: {e}")
    return None

def _get_tropical_cyclone_info() -> Dict[str, Any]:
    """
    Get tropical cyclone information and track from Hong Kong Observatory
    Returns active tropical cyclone warnings and forecast tracks
    """
    try:
        # HKO Tropical Cyclone Track API
        tc_url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=wtc&lang=en"
        response = requests.get(tc_url, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            
            # Check if there are active tropical cyclones
            tc_info = data.get("tropicalCycloneInfo", [])
            if not tc_info:
                return {
                    "source": "Hong Kong Observatory",
                    "active_cyclones": 0,
                    "message": "No active tropical cyclone at the moment"
                }
            
            cyclones = []
            for tc in tc_info:
                cyclone_data = {
                    "name": tc.get("nameOfTropicalCyclone"),
                    "name_chinese": tc.get("tropicalCycloneNameChinese"),
                    "category": tc.get("tropicalCycloneCategory"),
                    "intensity": tc.get("intensity"),
                    "position": tc.get("position"),
                    "movement": tc.get("movement"),
                    "max_wind": tc.get("maxSustainedWind"),
                    "warning_signal": tc.get("tcWarningSignal"),
                    "update_time": tc.get("updateTime")
                }
                
                # Get forecast track if available
                forecast_track = tc.get("forecastTrack", [])
                if forecast_track:
                    cyclone_data["forecast_positions"] = [{
                        "time": pos.get("forecastTime"),
                        "latitude": pos.get("latitude"),
                        "longitude": pos.get("longitude"),
                        "max_wind": pos.get("maxWind")
                    } for pos in forecast_track]
                
                cyclones.append(cyclone_data)
            
            return {
                "source": "Hong Kong Observatory",
                "active_cyclones": len(cyclones),
                "cyclones": cyclones,
                "update_time": data.get("updateTime")
            }
    except Exception as e:
        logger.debug(f"Error fetching tropical cyclone info: {e}")
    return None

def _get_air_quality(lat: float, lon: float, city: str = None) -> Dict[str, Any]:
    """
    Get air quality data for coordinates
    Includes both standard AQI and Hong Kong AQHI when applicable
    """
    air_quality_data = {}
    
    # Standard AQI from OpenWeather
    try:
        aqi_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY
        }
        response = requests.get(aqi_url, params=params, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            if data.get("list"):
                aqi_data = data["list"][0]
                aqi_level = aqi_data["main"]["aqi"]
                aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
                components = aqi_data.get("components", {})
                air_quality_data.update({
                    "aqi": aqi_level,
                    "aqi_label": aqi_labels.get(aqi_level, "Unknown"),
                    "pm2_5": components.get("pm2_5"),
                    "pm10": components.get("pm10"),
                    "no2": components.get("no2"),
                    "o3": components.get("o3"),
                    "co": components.get("co"),
                    "so2": components.get("so2")
                })
    except Exception as e:
        logger.error(f"Error fetching AQI: {e}")
    
    # Hong Kong AQHI (if querying Hong Kong)
    if city and "Hong Kong" in city:
        hk_aqhi = _get_hk_aqhi()
        if hk_aqhi:
            air_quality_data["aqhi"] = hk_aqhi
            logger.info(f"Hong Kong AQHI: {hk_aqhi.get('aqhi')} ({hk_aqhi.get('health_risk')})")
    
    return air_quality_data if air_quality_data else None

def _get_forecast(lat: float, lon: float, days: int = 10) -> List[Dict[str, Any]]:
    """Get weather forecast for next N days using One Call API"""
    try:
        # Note: One Call API 3.0 requires subscription, using 5 day forecast as alternative
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "cnt": min(days * 8, 40)  # 8 data points per day, max 40 (5 days)
        }
        response = requests.get(forecast_url, params=params, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            data = response.json()
            forecast_list = []
            for item in data.get("list", [])[:days * 8]:
                forecast_list.append({
                    "date": item["dt_txt"],
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "humidity": item["main"]["humidity"],
                    "conditions": item["weather"][0]["description"],
                    "wind_speed": item["wind"]["speed"],
                    "rain_probability": item.get("pop", 0) * 100
                })
            return forecast_list
    except Exception as e:
        logger.error(f"Error fetching forecast: {e}")
    return []

def get_weather_data(entities: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Fetch comprehensive weather data from OpenWeatherMap API
    
    Includes:
    - Current weather conditions
    - Air quality index (AQI) and pollutants
    - 10-day weather forecast
    
    Args:
        entities: Entity dictionary with location names
        
    Returns:
        Dictionary with comprehensive weather data for all requested locations
    """
    if not OPENWEATHER_API_KEY:
        logger.warning(f"{LOG_PREFIX_WEATHER_API} {LOG_RETRIEVAL_WEATHER_NO_KEY}")
        return {"error": "Missing API key", "domain": DOMAIN_WEATHER}
    
    # Check locations from LLM entity extraction
    locations = entities.get(ENTITY_KEY_LOCATIONS, [])
    cities = _extract_cities_from_locations(locations)
    
    # Fetch comprehensive weather data for all cities
    results = []
    for city in cities:
        try:
            # Get current weather
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                data = response.json()
                lat = data["coord"]["lat"]
                lon = data["coord"]["lon"]
                
                # Build comprehensive result
                result = {
                    "city": city,
                    "coordinates": {"lat": lat, "lon": lon},
                    "current": {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "conditions": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"],
                        "visibility": data.get("visibility"),
                        "clouds": data.get("clouds", {}).get("all")
                    }
                }
                
                # Add air quality data (includes AQHI for Hong Kong)
                air_quality = _get_air_quality(lat, lon, city)
                if air_quality:
                    result["air_quality"] = air_quality
                    # Log AQI
                    if "aqi" in air_quality:
                        logger.info(f"Air quality for {city}: {air_quality['aqi_label']} (AQI: {air_quality['aqi']})")
                    # Log AQHI for Hong Kong
                    if "aqhi" in air_quality:
                        aqhi_data = air_quality["aqhi"]
                        logger.info(f"Hong Kong AQHI: {aqhi_data.get('aqhi')} ({aqhi_data.get('health_risk')})")
                
                # Add HKO forecast for Hong Kong
                if "Hong Kong" in city:
                    hko_forecast = _get_hko_forecast()
                    if hko_forecast:
                        result["hko_forecast"] = hko_forecast
                        logger.info(f"Retrieved HKO 9-day forecast for Hong Kong")
                    
                    # Add tropical cyclone information
                    tc_info = _get_tropical_cyclone_info()
                    if tc_info:
                        result["tropical_cyclone"] = tc_info
                        if tc_info.get("active_cyclones", 0) > 0:
                            logger.info(f"Active tropical cyclones: {tc_info['active_cyclones']}")
                        else:
                            logger.info("No active tropical cyclones")
                
                # Add forecast data (next 5 days)
                forecast = _get_forecast(lat, lon, days=5)
                if forecast:
                    result["forecast"] = forecast
                    logger.info(f"Retrieved {len(forecast)} forecast data points for {city}")
                
                results.append(result)
                logger.info(f"{LOG_PREFIX_WEATHER_API} {LOG_RETRIEVAL_WEATHER_SUCCESS} {city}: {result['current']['temperature']}°C, {result['current']['conditions']}")
            else:
                logger.error(f"{LOG_PREFIX_WEATHER_API} {LOG_RETRIEVAL_WEATHER_FAILED} {city} with status {response.status_code}")
                results.append({"city": city, "error": "Weather API failed"})
                
        except Exception as e:
            logger.error(f"{LOG_PREFIX_WEATHER_API} {LOG_RETRIEVAL_WEATHER_ERROR} {city}: {e}")
            results.append({"city": city, "error": str(e)})
    
    return {
        "domain": DOMAIN_WEATHER,
        "locations": results,
        "source": "openweathermap",
        "multiple": len(results) > 1,
        "features": {
            "current_weather": True,
            "air_quality": True,
            "forecast_days": 5,  # Free tier provides 5 days
            "hko_forecast": any("Hong Kong" in r.get("city", "") for r in results),
            "tropical_cyclone_tracking": any("Hong Kong" in r.get("city", "") for r in results)
        }
    }

# Finance API 

def get_finance_data(entities: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Fetches financial data (FX, crypto, gold, stock) based on entities.
    entities: {
        "currencies": ["USD", "HKD"],
        "coins": ["bitcoin", "ethereum"],
        "commodities": ["gold"],
        "stocks": ["hsi"]
    }
    """
    try:
        # ---------------- FX ----------------
        currencies = entities.get("currencies", [])
        if len(currencies) >= 2:
            base_currency = currencies[0].upper()
            target_currency = currencies[1].upper()
        elif len(currencies) == 1:
            base_currency = currencies[0].upper()
            target_currency = "HKD" if base_currency != "HKD" else "USD"
        else:
            base_currency = "HKD"
            target_currency = "USD"

        # Amount if provided
        amount = entities.get("amount", [1])
        amount = float(amount[0]) if amount else 1

        # FX conversion
        if "fx" in entities or len(currencies) >= 1:
            fx_url = f"https://api.exchangerate.host/latest?base={base_currency}&symbols={target_currency}"
            fx_data = requests.get(fx_url, timeout=5).json()
            rate = fx_data.get("rates", {}).get(target_currency)
            if rate:
                converted = round(amount * rate, 2)
                return {
                    "topic": "finance",
                    "type": "fx",
                    "base": base_currency,
                    "target": target_currency,
                    "rate": rate,
                    "amount": amount,
                    "converted_amount": converted
                }
                
        # ---------------- CRYPTO ----------------
        coins = entities.get("coins", [])
        if coins:
            crypto_id = coins[0].lower()
            try:
                r = requests.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=hkd,usd",
                    timeout=5
                ).json()
                return {
                    "topic": "finance",
                    "type": "crypto",
                    "coin": crypto_id,
                    "price_hkd": r[crypto_id]["hkd"],
                    "price_usd": r[crypto_id]["usd"]
                }
            except:
                return {"error": "CRYPTO_API_FAILED"}

        # ---------------- STOCKS & COMMODITIES ----------------
        # stock_symbols now contains both stock tickers and commodity futures symbols
        symbols = entities.get("stock_symbols", [])
        if symbols:
            results = []
            for symbol in symbols:
                symbol = symbol.strip()
                
                # Determine if this is a commodity (continuous/futures contract with =F)
                is_commodity = symbol.endswith("=F")
                
                try:
                    # Use yfinance to fetch data (works for both stocks and commodities)
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # Get current price and previous close
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
                    
                    result_info = {
                        "symbol": symbol,
                        "type": "commodity" if is_commodity else "stock",
                        "name": info.get('longName') or info.get('shortName', symbol),
                        "current_price": current_price,
                        "previous_close": previous_close,
                        "change": None,
                        "change_percent": None,
                        "currency": info.get('currency', 'USD'),
                        "exchange": info.get('exchange'),
                        "market_state": info.get('marketState')
                    }
                    
                    # Add volume and market cap for stocks (not relevant for commodities)
                    if not is_commodity:
                        result_info["volume"] = info.get('volume')
                        result_info["market_cap"] = info.get('marketCap')
                    
                    # Calculate change if both values available
                    if result_info["current_price"] and result_info["previous_close"]:
                        result_info["change"] = round(result_info["current_price"] - result_info["previous_close"], 2)
                        result_info["change_percent"] = round((result_info["change"] / result_info["previous_close"]) * 100, 2)
                    
                    # For commodities, add HKD conversion
                    if is_commodity and result_info["current_price"]:
                        try:
                            fx_url = "https://api.exchangerate.host/latest?base=USD&symbols=HKD"
                            fx_response = requests.get(fx_url, timeout=5)
                            fx_data = fx_response.json()
                            usd_to_hkd = fx_data.get("rates", {}).get("HKD", 7.8)
                            
                            result_info["price_hkd"] = round(result_info["current_price"] * usd_to_hkd, 2)
                            result_info["previous_close_hkd"] = round(result_info["previous_close"] * usd_to_hkd, 2) if result_info["previous_close"] else None
                            logger.info(f"Commodity HKD conversion: {result_info['current_price']} USD = {result_info['price_hkd']} HKD")
                        except Exception as e:
                            logger.warning(f"Failed to convert commodity to HKD: {e}")
                    
                    results.append(result_info)
                    logger.info(f"{'Commodity' if is_commodity else 'Stock'} data retrieved for {symbol}: {result_info['name']} @ {result_info['current_price']} {result_info['currency']}")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch data for {symbol}: {e}")
                    results.append({
                        "symbol": symbol,
                        "type": "commodity" if is_commodity else "stock",
                        "error": f"Failed to fetch data: {str(e)}"
                    })
            
            if results:
                # Separate stocks and commodities for clearer response
                stocks = [r for r in results if r.get("type") == "stock" and "error" not in r]
                commodities = [r for r in results if r.get("type") == "commodity" and "error" not in r]
                errors = [r for r in results if "error" in r]
                
                response = {
                    "topic": "finance",
                    "count": len(results)
                }
                
                if stocks:
                    response["stocks"] = stocks
                if commodities:
                    response["commodities"] = commodities
                if errors:
                    response["errors"] = errors
                
                # Set type based on what we have
                if stocks and commodities:
                    response["type"] = "mixed"
                elif commodities:
                    response["type"] = "commodity"
                else:
                    response["type"] = "stock"
                
                return response
            else:
                return {"error": "FINANCE_API_FAILED"}

        # default fallback
        return {"error": "No recognizable finance query detected"}

    except Exception as e:
        return {"error": f"Finance API failed: {e}", "fallback": serpapi_search("finance " + str(entities))}

# -------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------
KMB = "https://data.etabus.gov.hk/v1/transport/kmb"
CITYBUS = "https://rt.data.gov.hk/v1/transport/citybus-nwfb"
MTR = "https://rt.data.gov.hk/v1/transport/mtr"
TD_JOURNEY = "https://data.hktransport.gov.hk/pt-platform/jp-api/journey"

def get_transportation_data(query: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Returns transportation route information using Google Maps Directions-like search.
    Uses web search to find public transit routes since TD Journey API is unavailable.
    """
    # Extract locations from entities
    locations = entities.get("locations", [])
    location_entities = [loc.strip() for loc in locations if loc.strip()]

    # Determine start and end
    start = None
    end = None
    
    if len(location_entities) >= 2:
        start = location_entities[0]
        end = location_entities[-1]
    elif len(location_entities) == 1:
        # Single location - assume going TO that location
        end = location_entities[0]
    
    # Try regex pattern "from X to Y" if locations not clear
    if not start or not end:
        match = re.search(r"(?:from|從)\s+([^\s]+(?:\s+[^\s]+)*)\s+(?:to|去|到)\s+([^\s?]+(?:\s+[^\s?]+)*)", query, re.IGNORECASE)
        if match:
            start = match.group(1).strip()
            end = match.group(2).strip()
    
    # Build search query for transportation
    if start and end:
        search_query = f"how to get from {start} to {end} Hong Kong public transport MTR bus"
        logger.info(f"{LOG_PREFIX_TRANSPORT_API} Transportation route: {start} → {end}")
    elif end:
        search_query = f"how to get to {end} Hong Kong public transport directions"
        logger.info(f"{LOG_PREFIX_TRANSPORT_API} Transportation to: {end}")
    else:
        # Fallback to original query
        search_query = query + " Hong Kong transport directions"
        logger.info(f"{LOG_PREFIX_TRANSPORT_API} Generic transportation query")
    
    # Use web search to find transportation information
    try:
        logger.info(f"{LOG_PREFIX_TRANSPORT_API} Using web search for route information")
        web_results = serpapi_search(search_query, max_results=5)
        
        if web_results:
            # Format as structured response with web results
            return {
                "topic": "transportation",
                "start": start,
                "end": end,
                "search_query": search_query,
                "method": "web_search",
                "results": web_results,
                "message": "Transportation directions retrieved from web search"
            }
        else:
            return {"error": "No transportation results found", "domain": "transportation"}
            
    except Exception as e:
        logger.error(f"{LOG_PREFIX_TRANSPORT_API} Web search failed: {e}")
        return {"error": f"Transportation search failed: {e}", "domain": "transportation"}


@timed_operation("call_domain_api")
def call_domain_api(query: str, domain: str, understanding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call appropriate domain-specific API based on classified domain
    
    Routes to finance, weather, or transportation APIs based on domain.
    
    Args:
        query: User's query string
        domain: Classified domain (finance, weather, transportation)
        understanding: Query understanding with entities
        
    Returns:
        Structured data from external API or error dictionary
    """
    entities = understanding.get("entities", {
        ENTITY_KEY_LOCATIONS: [],
        ENTITY_KEY_ORGANIZATIONS: [],
        "dates": [],
        "products": [],
        "general": []
    })
    
    logger.info(f"[Domain API] Calling {domain} API for query: {query}")
    
    if domain == DOMAIN_FINANCE:
        result = get_finance_data(entities)
        print(result)
    elif domain == DOMAIN_WEATHER:
        result = get_weather_data(entities)
    elif domain == DOMAIN_TRANSPORTATION:
        result = get_transportation_data(query, entities)
    else:
        logger.warning(f"[Domain API] No handler for domain: {domain}")
        result = {"error": f"No API handler for domain: {domain}", "domain": domain}
    
    # Log if domain API fails (let pipeline handle fallback)
    if "error" in result:
        logger.error(f"[Domain API] {domain} API returned error: {result.get('error')}")
    
    return result

def retrieve_information(query: str, understanding: Dict[str, Any], sources: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main retrieval function that coordinates multiple information sources
    
    Retrieves from local KB, web search, and domain APIs based on
    source selection strategy.
    
    Args:
        query: User's search query
        understanding: Query understanding with intent, domain, entities
        sources: Source selection with sources list, domain handler, priority
        
    Returns:
        Dictionary with local_kb_results, web_results, and domain_api_results
    """
    results = {
        "local_kb_results": [],
        "web_results": [],
        "domain_api_results": {}
    }
    
    source_list = sources.get("sources", [])
    domain_handler = sources.get("domain_handler")
    priority = sources.get("priority", [])
    
    # Extract user context from understanding
    user_context = understanding.get("user_context")
    
    logger.info(f"\n[Retrieval] Starting retrieval from sources: {source_list}")
    logger.info(f"[Retrieval] Priority order: {priority}")
    if user_context and isinstance(user_context, dict):
        location = user_context.get('location', 'Unknown')
        country = user_context.get('country', '')
        current_time = user_context.get('current_time', 'Unknown')
        location_str = f"{location}, {country}" if country else location
        logger.info(f"[Retrieval] User context: {location_str}, {current_time}")
    
    # Retrieve from local knowledge base (vector search)
    if SOURCE_LOCAL_KB in source_list:
        logger.info("[Retrieval] Querying local knowledge base...")
        kb_results = retrieve_from_local_kb(query)
        
    # Only add HKGAI direct answer when web search is NOT used
    if SOURCE_WEB_SEARCH not in source_list:
        logger.info("[Retrieval] Web search not used - allowing HKGAI direct answer")
        hkgai_result = get_hkgai_answer(query)
        if hkgai_result:
            kb_results.insert(0, hkgai_result)
    else:
        logger.info("[Retrieval] Web search enabled - skipping HKGAI direct answer to prevent hallucinations")
    
    results["local_kb_results"] = kb_results
    logger.info(f"[Retrieval] Found {len(kb_results)} results from local KB")
    
    # Retrieve from web search (Google Custom Search)
    if SOURCE_WEB_SEARCH in source_list:
        logger.info("[Retrieval] Querying web search...")
        web_results = retrieve_from_web(query, user_context)
        results["web_results"] = web_results
        logger.info(f"[Retrieval] Found {len(web_results)} results from web search")
    
    # Call domain-specific API (weather, finance, transportation)
    if SOURCE_DOMAIN_API in source_list and domain_handler:
        logger.info(f"[Retrieval] Calling domain API: {domain_handler}")
        api_result = call_domain_api(query, domain_handler, understanding)
        results["domain_api_results"] = api_result
        
        # If domain API fails and web search not already used, fallback to web
        if "error" in api_result and SOURCE_WEB_SEARCH not in source_list:
            logger.warning("[Retrieval] Domain API failed, falling back to web search")
            fallback_results = retrieve_from_web(query, user_context)
            results["web_results"] = fallback_results
            logger.info(f"[Retrieval] Fallback web search found {len(fallback_results)} results")
    
    # Summary
    _log_retrieval_summary(results)
    
    return results
