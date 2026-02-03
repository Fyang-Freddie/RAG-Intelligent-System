"""
Centralized Configuration - All magic numbers, strings, and thresholds
Prevents hardcoded values scattered throughout the codebase
"""

# ============================================================================
# VISION MODEL CONFIGURATION
# ============================================================================
VISION_MODEL_NAME = 'minicpm-v'
VISION_TEMPERATURE_CLASSIFY = 0.0
VISION_TEMPERATURE_EXTRACT = 0.3
VISION_PREVIEW_LENGTH = 100

# ============================================================================
# IMAGE PROCESSING CONSTANTS
# ============================================================================
IMAGE_FORMAT_RGB = 'RGB'
TEMP_IMAGE_SUFFIX = '.png'
TEMP_IMAGE_FORMAT = 'PNG'

# Image Classification Types
IMAGE_TYPE_TEXT_SCREENSHOT = "text_screenshot"
IMAGE_TYPE_COMPLEX = "complex_image"
IMAGE_TYPE_UNKNOWN = "unknown"

# Extraction Methods
EXTRACTION_METHOD_OCR_FAST = 'ocr_fast'
EXTRACTION_METHOD_VISION_AI = 'vision_ai'
EXTRACTION_METHOD_OCR_FALLBACK = 'ocr_fallback'

# ============================================================================
# FILE TYPE CONSTANTS
# ============================================================================
FILE_TYPE_IMAGE = 'image'
FILE_TYPE_PDF = 'pdf'
FILE_TYPE_DOCX = 'docx'
FILE_TYPE_TEXT = 'text'

# Supported File Extensions
SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
SUPPORTED_PDF_EXTENSIONS = ['.pdf']
SUPPORTED_DOCX_EXTENSIONS = ['.docx']
SUPPORTED_TEXT_EXTENSIONS = ['.txt']

# ============================================================================
# TEXT ENCODING
# ============================================================================
TEXT_ENCODING_UTF8 = 'utf-8'
TEXT_ENCODING_LATIN1 = 'latin-1'

# ============================================================================
# VISION MODEL PROMPTS
# ============================================================================
PROMPT_CLASSIFY_IMAGE = (
    'Is this image a simple screenshot of text/document (like a screenshot of a '
    'webpage, PDF, or text editor)? Answer ONLY with "yes" or "no". Answer "yes" '
    'if it\'s primarily text on a plain background. Answer "no" if it contains '
    'photos, graphics, complex layouts, handwriting, or real-world objects.'
)

PROMPT_EXTRACT_TEXT = (
    "Please extract all text from this image, maintaining the original layout. "
    "Additionally, provide a detailed description of the main subject's shape and "
    "color, along with the building situated behind it. Conclude with 3 specific "
    "keywords that would help me identify this object online."
)

# ============================================================================
# DOCUMENT SEPARATORS
# ============================================================================
PDF_PAGE_SEPARATOR = '\n\n'
DOCX_LINE_SEPARATOR = '\n'
DOCX_TABLE_CELL_SEPARATOR = '\t'

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_UNSUPPORTED_FILE_TYPE = 'Unsupported file type'
ERROR_HANDLER_NOT_IMPLEMENTED = 'Handler not implemented for'
ERROR_FILE_PROCESSING_FAILED = 'Error processing file'
ERROR_IMAGE_PROCESSING_FAILED = 'Image processing failed'
ERROR_PDF_EXTRACTION_FAILED = 'PDF extraction failed'
ERROR_DOCX_EXTRACTION_FAILED = 'DOCX extraction failed'
ERROR_TEXT_EXTRACTION_FAILED = 'Text extraction failed'
ERROR_BOTH_METHODS_FAILED = 'Both vision model and OCR failed'

# ============================================================================
# LOG MESSAGES
# ============================================================================
LOG_VISION_MODEL_NOT_FOUND = "not found in Ollama. Run: ollama pull"
LOG_VISION_CONNECTION_ERROR = "Ollama connection error"
LOG_CLASSIFYING_IMAGE = "Classifying image type..."
LOG_IMAGE_TYPE_TEXT = "Classification: Simple text screenshot"
LOG_IMAGE_TYPE_COMPLEX = "Classification: Complex image"
LOG_CLASSIFICATION_ERROR = "Classification error"
LOG_EXTRACTING_TEXT = "Extracting text from image with"
LOG_EXTRACTED_TEXT_PREFIX = "Extracted text"
LOG_EMPTY_RESPONSE = "Empty response from model"
LOG_VISION_ERROR = "Vision Model Error"
LOG_USING_OCR_FAST = "Using fast OCR for text screenshot"
LOG_USING_VISION = "Using vision model for complex image"
LOG_OCR_FAILED_FALLBACK = "OCR failed, falling back to vision model"
LOG_VISION_UNAVAILABLE = "Vision model unavailable, falling back to pytesseract OCR..."

# ============================================================================
# WARNING MESSAGES
# ============================================================================
WARNING_VISION_MODEL_UNAVAILABLE = 'Vision model unavailable, using pytesseract OCR'

# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================

# Query Intent Types
INTENT_ANALYTICAL = "analytical"
INTENT_FACTUAL = "factual"
INTENT_CONVERSATIONAL = "conversational"
INTENT_TRANSACTIONAL = "transactional"

# Query Domain Types
DOMAIN_WEATHER = "weather"
DOMAIN_TRANSPORTATION = "transportation"
DOMAIN_FINANCE = "finance"
DOMAIN_GENERAL = "general"

# Valid Values Lists
VALID_INTENTS = [INTENT_ANALYTICAL, INTENT_FACTUAL, INTENT_CONVERSATIONAL, INTENT_TRANSACTIONAL]
VALID_DOMAINS = [DOMAIN_WEATHER, DOMAIN_TRANSPORTATION, DOMAIN_FINANCE, DOMAIN_GENERAL]

# Source Types
SOURCE_LOCAL_KB = "local_kb"
SOURCE_DOMAIN_API = "domain_api"
SOURCE_WEB_SEARCH = "web_search"

# Result Sources
RESULT_SOURCE_LOCAL_KB = "local_kb"
RESULT_SOURCE_WEB = "web"
RESULT_SOURCE_GOOGLE_SEARCH = "google_search"
RESULT_SOURCE_DOMAIN_API = "domain_api"

# Default Scores
DEFAULT_SCORE_LOCAL_KB = 0.5
DEFAULT_SCORE_WEB = 0.7
DEFAULT_SCORE_DOMAIN_API = 0.9
DEFAULT_SCORE_WEB_RESULTS = 0.8

# Search Limits
DEFAULT_TOP_K_LOCAL_KB = 5
DEFAULT_MAX_WEB_RESULTS = 5
DEFAULT_MAX_CONTEXT_RESULTS = 5
DEFAULT_MAX_SUPPORTING_WEB = 3

# API Timeouts
API_TIMEOUT_SECONDS = 10

# Temperature Settings
TEMPERATURE_LLM_CLASSIFICATION = 0.1
TEMPERATURE_RESPONSE_GENERATION = 0.7

# Token Limits
MAX_TOKENS_LLM_CLASSIFICATION = 200
MAX_TOKENS_RESPONSE_GENERATION = 800

# BM25 Reranking Weights
BM25_WEIGHT_ORIGINAL = 0.7
BM25_WEIGHT_BM25 = 0.3

# Content Preview Lengths
CONTENT_PREVIEW_LENGTH_SHORT = 50
CONTENT_PREVIEW_LENGTH_MEDIUM = 200

# Entity Keys
ENTITY_KEY_LOCATIONS = "locations"
ENTITY_KEY_ORGANIZATIONS = "organizations"
ENTITY_KEY_STOCK_SYMBOLS = "stock_symbols"
ENTITY_KEY_DATES = "dates"
ENTITY_KEY_PRODUCTS = "products"
ENTITY_KEY_GENERAL = "general"

# ============================================================================
# PIPELINE LOG MESSAGES
# ============================================================================
LOG_PIPELINE_UNDERSTANDING = "Understanding"
LOG_PIPELINE_SOURCES = "Sources"
LOG_PIPELINE_RETRIEVAL_START = "Starting retrieval..."
LOG_PIPELINE_RETRIEVAL_TOTAL = "Retrieved"
LOG_PIPELINE_RERANKING = "Reranking results..."
LOG_PIPELINE_RERANKED = "Reranked to"
LOG_PIPELINE_GENERATING = "Generating response..."
LOG_PIPELINE_SUCCESS = "✅ Pipeline completed successfully"
LOG_PIPELINE_ERROR = "Pipeline Error"

# Query Understanding Logs
LOG_QU_API_ERROR = "API Error"
LOG_QU_EMPTY_RESPONSE = "Empty response from API"
LOG_QU_INVALID_FORMAT = "Invalid response format"
LOG_QU_INVALID_INTENT = "Invalid intent"
LOG_QU_INVALID_DOMAIN = "Invalid domain"
LOG_QU_CLASSIFICATION_SUCCESS = "Intent"
LOG_QU_ENTITIES = "Entities"
LOG_QU_JSON_ERROR = "JSON parse error"
LOG_QU_RAW_CONTENT = "Raw content"
LOG_QU_ERROR = "Error"
LOG_QU_FAILED_DEFAULTS = "LLM classification failed, using defaults"
LOG_QU_RESULT = "Intent"

# Source Selection Logs
LOG_SS_FINANCE_API = "Using Finance API (real-time stock/market data)"
LOG_SS_WEATHER_API = "Using Weather API (real-time forecasts)"
LOG_SS_TRANSPORT_API = "Using Transportation API (routes/schedules/traffic)"
LOG_SS_WEB_GENERAL = "Using Web Search (general knowledge/current events)"
LOG_SS_WEB_SUPPLEMENTARY = "Adding Web Search (supplementary real-time data)"
LOG_SS_KB_PRIMARY = "Using Local KB (primary source for static knowledge)"
LOG_SS_KB_SUPPLEMENTARY = "Using Local KB (supplementary context)"
LOG_SS_FINAL = "Final: Sources"

# Retrieval Logs
LOG_RETRIEVAL_KB_UNAVAILABLE = "Retriever not available, returning empty results"
LOG_RETRIEVAL_KB_FOUND = "Found"
LOG_RETRIEVAL_KB_ERROR = "Search error"
LOG_RETRIEVAL_WEB_NO_API_KEY = "Missing GOOGLE_SEARCH_API_KEY"
LOG_RETRIEVAL_WEB_NO_CX = "Missing GOOGLE_CX_ID"
LOG_RETRIEVAL_WEB_NO_RESULTS = "No results found for"
LOG_RETRIEVAL_WEB_FOUND = "Found"
LOG_RETRIEVAL_WEB_API_FAILED = "API failed with status"
LOG_RETRIEVAL_WEB_ERROR = "Error"
LOG_RETRIEVAL_WEATHER_NO_KEY = "Missing OPENWEATHER_API_KEY"
LOG_RETRIEVAL_WEATHER_SUCCESS = "Retrieved weather for"
LOG_RETRIEVAL_WEATHER_FAILED = "Failed for"
LOG_RETRIEVAL_WEATHER_ERROR = "Error for"
LOG_RETRIEVAL_FINANCE_NO_ORGS = "No organizations found in entities"
LOG_RETRIEVAL_FINANCE_MAPPED = "Mapped"
LOG_RETRIEVAL_FINANCE_AS_IS = "Using"
LOG_RETRIEVAL_FINANCE_SUCCESS = "Retrieved"
LOG_RETRIEVAL_FINANCE_NOT_FOUND = "Symbol"
LOG_RETRIEVAL_FINANCE_FAILED = "Failed for"
LOG_RETRIEVAL_FINANCE_ERROR = "Error for"
LOG_RETRIEVAL_TRANSPORT_NO_KEY = "Missing TRANSPORT_API_KEY"

# Reranking Logs
LOG_RERANKING_BM25_ERROR = "BM25 reranking error"

# Response Generation Logs
LOG_RESPONSE_ERROR = "I apologize, but I encountered an error generating a response."
LOG_RESPONSE_FALLBACK = "I couldn't generate a response at this time."

# Component Log Prefixes
LOG_PREFIX_PIPELINE = "[Pipeline]"
LOG_PREFIX_LLM_CLASSIFICATION = "[LLM Classification]"
LOG_PREFIX_QUERY_UNDERSTANDING = "[Query Understanding]"
LOG_PREFIX_SOURCE_SELECTION = "[Source Selection]"
LOG_PREFIX_RETRIEVAL = "[Retrieval]"
LOG_PREFIX_LOCAL_KB = "[Local KB]"
LOG_PREFIX_WEB_SEARCH = "[Web Search]"
LOG_PREFIX_WEATHER_API = "[Weather API]"
LOG_PREFIX_FINANCE_API = "[Finance API]"
LOG_PREFIX_TRANSPORT_API = "[Transportation API]"

# ============================================================================
# PIPELINE ERROR MESSAGES
# ============================================================================
ERROR_PIPELINE_PROCESSING = "I apologize, but I encountered an error processing your query"

# ============================================================================
# LLM CLASSIFICATION PROMPT
# ============================================================================
LLM_CLASSIFICATION_SYSTEM_PROMPT = """You are a multilingual query classification assistant. Analyze the user's query (in English or Chinese) and classify it into:

                            INTENT (choose one):
                            - analytical: Comparing, analyzing, evaluating multiple options (比較、分析、評估)
                            - factual: Seeking specific information or facts (尋求具體資訊或事實)
                            - conversational: Greetings, small talk, general chat (問候、閒聊)
                            - transactional: Booking, purchasing, scheduling, ordering (預訂、購買、安排)

                            DOMAIN (choose one):
                            - weather: Weather forecasts, temperature, rain, climate (天氣預報、溫度、雨、氣候)
                            - transportation: Routes, schedules, traffic, public transit (路線、時間表、交通、公共交通)
                            - finance: Stocks, markets, investments, currencies, earnings (股票、市場、投資、貨幣)
                            - general: Everything else (restaurants, hotels, general knowledge, etc.) (餐廳、酒店、一般知識等)

                            NEEDS_WEB (boolean):
                            Determine if this query requires web search/real-time data. Set to true if:
                            - Query asks for current/real-time information (weather now, stock prices today, traffic conditions)
                            問及當前/即時資訊（現在天氣、今日股價、交通狀況）
                            - Query asks about recent events not in your training data (cutoff: April 2024)
                            問及訓練資料之後的近期事件(截止: 2024年4月)
                            - Query asks about time-sensitive data (today, now, current, latest, this week, 2024, 2025)
                            問及時效性資料（(今天、現在、當前、最新、本週、2024、2025)
                            - Query is in finance/weather/transportation domain (usually needs real-time data)
                            金融/天氣/交通領域的查詢（通常需要即時資料）
                            - Query asks about SPECIFIC locations, buildings, sculptures, artworks, or places (needs specific details)
                            問及具體地點、建築物、雕塑、藝術品或場所（需要具體細節）
                            - Query asks to identify, locate, or find specific things ("where is X", "identify this", "what is this")
                            要求識別、定位或查找具體事物（"X在哪裡"、"識別這個"、"這是什麼"）
                            - Query about campus locations, buildings, facilities, or specific venue information
                            問及校園位置、建築、設施或特定場所資訊
                            Set to false if:
                            - Query asks about general knowledge, history, or facts from before April 2024
                            問及一般知識、歷史或2024年4月之前的事實
                            - Query is conversational/greeting
                            對話/問候
                            - Query can be answered with general knowledge (not specific locations/objects)
                            可用一般知識回答（非具體位置/物品）

                            ENTITIES (extract domain-specific entities):
                            - locations: City names, place names, addresses - MUST capitalize each word (城市名、地點名、地址 - 必須首字母大寫)
                              Examples: "Tokyo", "Hong Kong", "New York", "San Francisco"
                            - organizations: Company/organization names (公司/組織名稱)
                            - stock_symbols: Stock AND COMMODITY ticker symbols for Yahoo Finance API (股票及商品代號)
                              CRITICAL: Return proper Yahoo Finance symbols for BOTH stocks and commodities:
                              
                              STOCKS (uppercase):
                              * US Stocks: "AAPL" (Apple), "MSFT" (Microsoft), "GOOGL" (Google), "AMZN" (Amazon), "TSLA" (Tesla), "NVDA" (Nvidia)
                              * HK Stocks: Add ".HK" suffix - "0700.HK" (Tencent/騰訊), "9988.HK" (Alibaba), "0941.HK" (China Mobile)
                              * Indices: "^HSI" (Hang Seng/恒生指數), "^DJI" (Dow Jones), "^GSPC" (S&P 500), "^IXIC" (Nasdaq)
                              * Chinese stocks: "BABA" (Alibaba US listing), "JD" (JD.com)
                              
                              COMMODITIES (use spot/continuous contract symbols):
                              * Precious Metals: "GC=F" (Gold), "SI=F" (Silver), "PL=F" (Platinum), "PA=F" (Palladium)
                              * Energy: "CL=F" (Crude Oil), "NG=F" (Natural Gas), "BZ=F" (Brent Crude)
                              * Industrial Metals: "HG=F" (Copper), "ALI=F" (Aluminum)
                              * Agriculture: "ZC=F" (Corn), "ZW=F" (Wheat), "ZS=F" (Soybeans)
                              
                              Note: =F symbols represent continuous/front-month contracts showing current market prices
                              
                              Examples: 
                              - "What's Apple stock price?" → stock_symbols: ["AAPL"]
                              - "Gold price today" → stock_symbols: ["GC=F"]
                              - "Tesla and silver prices" → stock_symbols: ["TSLA", "SI=F"]
                              - "How much is crude oil?" → stock_symbols: ["CL=F"]
                              - "Hang Seng Index and gold" → stock_symbols: ["^HSI", "GC=F"]
                              
                              If unsure of exact symbol, use best guess with proper format
                            - dates: Date/time references (today, tomorrow, this week, 今天, 明天, 本週)
                            - currencies: Currency codes for foreign exchange queries (貨幣代碼用於外匯查詢)
                              CRITICAL: Use 3-letter ISO currency codes in UPPERCASE:
                              * Major currencies: "USD", "EUR", "GBP", "JPY", "CNY", "HKD", "AUD", "CAD", "CHF", "SGD"
                              * Format: [from_currency, to_currency]
                              Examples:
                              - "Convert 100 USD to HKD" → currencies: ["USD", "HKD"], amount: [100]
                              - "What's the exchange rate for EUR to USD?" → currencies: ["EUR", "USD"]
                              - "How much is 50 pounds in Hong Kong dollars?" → currencies: ["GBP", "HKD"], amount: [50]
                              - "Exchange rate between yen and dollar" → currencies: ["JPY", "USD"]
                            - products: Product names (non-commodity products and services) (非商品類產品及服務)
                            - general: Any other important named entities

                            Return ONLY a valid JSON object with this exact format:
                            {
                            "intent": "analytical|factual|conversational|transactional",
                            "domain": "weather|transportation|finance|general",
                            "needs_web": true|false,
                            "entities": {
                                "locations": ["Capitalized", "Location", "Names"],
                                "organizations": ["Company", "Names"],
                                "stock_symbols": ["AAPL", "0700.HK", "^HSI", "GC=F"],
                                "currencies": ["HKD"],
                                "amount": [100],
                                "dates": ["list", "of", "dates"],
                                "products": ["product", "names"],
                                "general": ["other", "entities"]
                            }
                            }
                        """

LLM_CLASSIFICATION_USER_PROMPT_TEMPLATE = 'Classify this query: "{query}"'

# ============================================================================
# RESPONSE GENERATION PROMPTS
# ============================================================================
RESPONSE_GENERATION_SYSTEM_PROMPT_TEMPLATE = """You are HKGAI-V1, an intelligent assistant.

Query Intent: {intent}
Query Domain: {domain}

Provide a helpful, accurate, well-structured response using the context. If the user's query contains incorrect information or false premises (e.g., wrong numbers, incorrect facts), politely correct them using the context provided. Do not simply echo back incorrect information from the query."""

RESPONSE_GENERATION_USER_PROMPT_TEMPLATE = """User Query: {query}

{context_summary}

Based on the context provided, answer the user's query accurately. If the query contains factual errors (e.g., calling something "fourth" when context shows it's "third"), correct this misinformation in your response while still addressing the user's intent."""

RESPONSE_CONTEXT_HEADER = "Available context:\n"
RESPONSE_PRIMARY_SOURCE_HEADER = "\n[Primary Source: Real-time API Data]\n"
RESPONSE_SUPPORTING_WEB_HEADER = "\n[Supporting Information from Web]:\n"
RESPONSE_SOURCE_HEADER_TEMPLATE = "\n[Source {index}: {source}]\n"

# ============================================================================
# MARKDOWN CODE BLOCK MARKERS
# ============================================================================
MARKDOWN_JSON_START = "```json"
MARKDOWN_CODE_START = "```"
