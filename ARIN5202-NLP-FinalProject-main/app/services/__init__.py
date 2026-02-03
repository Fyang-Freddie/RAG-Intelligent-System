# Expose service clients
from .hkgenai import HKGAIClient
from .document_processor import get_document_processor, DocumentProcessor

__all__ = ["HKGAIClient", "get_document_processor", "DocumentProcessor"]
