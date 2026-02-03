import json
import re
import faiss
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from datasets import load_dataset

# Global lazy-loaded models

# Global cache for local retriever components
_local_retriever_cache = {
    "model": None,
    "index": None,
    "documents": None,
    "initialized": False
}

ML_AVAILABLE = True

def load_local_retriever():
    """
    Load FAISS index, metadata, and local embedding model.
    Uses caching to avoid reloading on every query.
    """
    # Return cached components if already loaded
    if _local_retriever_cache["initialized"]:
        return (
            _local_retriever_cache["model"],
            _local_retriever_cache["index"],
            _local_retriever_cache["documents"]
        )
    
    base_dir = "app/data/local_database/models"
    model_dir = "app/data/local_database/models/intfloat-multilingual-e5-small"
    
    base_path = Path(base_dir)
    index_path = base_path / "combined_kb_index.faiss"
    meta_path = base_path / "combined_kb_metadata.json"
    local_model_path = Path(model_dir)
    
    # Safety checks
    if not index_path.exists():
        print(f"[Local KB] Index not found: {index_path}")
        print("[Local KB] Please run build_faiss_index() to create the index first")
        return None, None, None
    
    if not meta_path.exists():
        print(f"[Local KB] Metadata not found: {meta_path}")
        return None, None, None
    
    if not local_model_path.exists():
        print(f"[Local KB] Model not found: {local_model_path}")
        return None, None, None
    
    try:
        # Load model
        print(f"[Local KB] Loading embedding model from: {local_model_path}")
        model = SentenceTransformer(str(local_model_path))
        
        # Load FAISS index
        print(f"[Local KB] Loading FAISS index from: {index_path}")
        index = faiss.read_index(str(index_path))
        
        # Load metadata
        print(f"[Local KB] Loading metadata from: {meta_path}")
        with open(meta_path, "r", encoding="utf-8") as f:
            documents = json.load(f)
        
        print(f"[Local KB] Successfully loaded {len(documents)} documents")
        
        # Cache the components
        _local_retriever_cache["model"] = model
        _local_retriever_cache["index"] = index
        _local_retriever_cache["documents"] = documents
        _local_retriever_cache["initialized"] = True
        
        return model, index, documents
        
    except Exception as e:
        print(f"[Local KB] Error loading retriever: {e}")
        return None, None, None

def prepare_knowledge_base(
    md_path: str = "app/data/local_database/fictional_knowledge_base.md",
    output_path: str = "app/data/local_database/models/combined_knowledge_base.json",
    include_wikipedia: bool = False
) -> List[Dict[str, str]]:
    """
    Prepare combined knowledge base from markdown and optional Wikipedia corpus.
    
    Args:
        md_path: Path to local markdown knowledge base
        output_path: Path to save combined JSON output
        include_wikipedia: Whether to include Wikipedia mini corpus
        
    Returns:
        List of documents with 'content' field
    """
    documents = []
    
    # 1. Load local Markdown KB (skip intro + ToC)
    md_path_obj = Path(md_path)
    if md_path_obj.exists():
        print(f"Loading local markdown: {md_path_obj}")
        with open(md_path_obj, "r", encoding="utf-8") as f:
            md_text = f.read()

        # Remove everything before the first real section
        if "## The Republic of Sereleia" in md_text:
            md_text = md_text.split("## The Republic of Sereleia", 1)[-1]
            md_text = "## The Republic of Sereleia\n" + md_text

        # Split into sections (##)
        sections = re.split(r"\n## ", md_text)
        fictional_docs = []

        for section in sections:
            section = section.strip()
            if not section:
                continue
            lines = section.splitlines()
            content = "\n".join(lines[1:]).strip()
            # Split into subsections (###)
            subsections = re.split(r"\n### ", content)
            if len(subsections) > 1:
                for sub in subsections:
                    sub = sub.strip()
                    if not sub:
                        continue
                    sub_lines = sub.splitlines()
                    sub_content = "\n".join(sub_lines[1:]).strip()
                    if sub_content:
                        fictional_docs.append({"content": sub_content})
            else:
                if content:
                    fictional_docs.append({"content": content})

        print(f"[✓] Loaded {len(fictional_docs)} content sections from markdown.")
        documents.extend(fictional_docs)
    
    # 2. Load Wikipedia corpus if requested
    if include_wikipedia:
        try:
            print("Loading Hugging Face dataset: rag-datasets/rag-mini-wikipedia (text_corpus)...")
            corpus = load_dataset("rag-datasets/rag-mini-wikipedia", name="text-corpus", split="passages")

            wiki_docs = []
            for item in corpus:
                content = item.get("passage") or item.get("text") or ""
                if content.strip():
                    wiki_docs.append({"content": content.strip()})

            print(f"[✓] Loaded {len(wiki_docs)} Wikipedia passages.")
            documents.extend(wiki_docs)
        except Exception as e:
            print(f"[Warning] Could not load Wikipedia dataset: {e}")
    
    # 3. Save combined dataset
    if documents:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path_obj, "w", encoding="utf-8") as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)

        print(f"[✓] Combined dataset saved to: {output_path_obj}")
        print(f"    Total entries: {len(documents)}")
    
    return documents

def build_faiss_index(
    json_path: str = "app/data/local_database/models/combined_knowledge_base.json",
    index_path: str = "app/data/local_database/models/combined_kb_index.faiss",
    meta_path: str = "app/data/local_database/models/combined_kb_metadata.json",
    model_name: str = "intfloat/multilingual-e5-small",
    local_model_path: str = "app/data/local_database/models/intfloat-multilingual-e5-small"
) -> tuple:
    """
    Build FAISS index from combined knowledge base JSON.
    
    Args:
        json_path: Path to combined knowledge base JSON
        index_path: Path to save FAISS index
        meta_path: Path to save metadata JSON
        model_name: Hugging Face model name
        local_model_path: Path to save/load model locally
        
    Returns:
        Tuple of (model, index, documents)
    """
    # 1. Load combined JSON
    json_path_obj = Path(json_path)
    if not json_path_obj.exists():
        print(f"[Error] {json_path_obj} not found. Run prepare_knowledge_base() first.")
        return None, None, None

    print(f"Loading combined knowledge base: {json_path_obj}")
    with open(json_path_obj, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"[✓] Loaded {len(documents)} documents for indexing.")

    # 2. Load or download embedding model locally
    local_model_path_obj = Path(local_model_path)

    if local_model_path_obj.exists():
        print(f"[✓] Loading embedding model locally from: {local_model_path_obj}")
        model = SentenceTransformer(str(local_model_path_obj))
    else:
        print(f"[↓] Downloading model from Hugging Face: {model_name}")
        model = SentenceTransformer(model_name)
        local_model_path_obj.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(local_model_path_obj))
        print(f"[✓] Model saved locally to: {local_model_path_obj}")

    # 3. Create embeddings
    texts = [doc["content"] for doc in documents]
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    print(f"[✓] Embeddings created. Shape: {embeddings.shape}")

    # 4. Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    index_path_obj = Path(index_path)
    index_path_obj.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path_obj))

    # Save metadata
    meta_path_obj = Path(meta_path)
    with open(meta_path_obj, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print("[✓] FAISS index and metadata saved.")
    print(f"   ├── {index_path_obj}")
    print(f"   └── {meta_path_obj}")
    
    return model, index, documents

def download_wikipedia_corpus(save_path: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Download and optionally save the RAG mini-Wikipedia corpus.
    
    Args:
        save_path: Optional path to save the corpus as JSON
        
    Returns:
        List of documents with 'content' field
    """
    try:
        print("Loading Hugging Face dataset: rag-datasets/rag-mini-wikipedia (text_corpus)...")
        corpus = load_dataset("rag-datasets/rag-mini-wikipedia", name="text-corpus", split="passages")
        
        documents = []
        for item in corpus:
            content = item.get("passage") or item.get("text") or ""
            if content.strip():
                documents.append({"content": content.strip()})
        
        print(f"[✓] Loaded {len(documents)} Wikipedia passages.")
        
        if save_path:
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path_obj, "w", encoding="utf-8") as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            print(f"[✓] Corpus saved to: {save_path_obj}")
        
        return documents
        
    except Exception as e:
        print(f"[Error] Could not download Wikipedia corpus: {e}")
        return []