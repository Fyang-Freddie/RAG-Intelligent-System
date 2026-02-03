# Expose classifier functions and ML utilities
from .classifiers import (
    load_local_retriever,
    prepare_knowledge_base,
    build_faiss_index,
    download_wikipedia_corpus,
    ML_AVAILABLE
)

__all__ = [
    "load_local_retriever",
    "prepare_knowledge_base",
    "build_faiss_index",
    "download_wikipedia_corpus",
    "ML_AVAILABLE"
]

