from flask import Flask
from pathlib import Path
from app.models.classifiers import load_local_retriever

def create_app():
    app = Flask(__name__)

    # Initialize models and local knowledge base on startup
    with app.app_context():
        initialize_models()
        setup_local_kb()

    # Import routes
    from app.routes import main
    app.register_blueprint(main)

    return app

def initialize_models():
    """Initialize all ML models on app startup."""
    print("\n[App Init] Initializing ML models...")
    
    # Pre-load local retriever (FAISS + embedding model)
    print("[App Init] Loading local retriever...")
    model, index, documents = load_local_retriever()
    if model and index and documents:
        print(f"[App Init] ✓ Local retriever loaded ({len(documents)} documents)")
    else:
        print("[App Init] ⚠ Local retriever not available")
    
    print("[App Init] Model initialization complete.\n")

def setup_local_kb():
    """Setup local knowledge base on app startup."""
    from app.models.classifiers import prepare_knowledge_base, build_faiss_index
    
    print("\n[App Init] Setting up local knowledge base...")
    
    # Check if index already exists
    index_path = Path("app/data/local_database/models/combined_kb_index.faiss")
    kb_json_path = Path("app/data/local_database/models/combined_knowledge_base.json")
    
    if index_path.exists() and kb_json_path.exists():
        print("[App Init] Local KB index already exists, skipping setup.")
        return
    
    # Step 1: Prepare knowledge base (download Wikipedia if needed)
    if not kb_json_path.exists():
        print("[App Init] Preparing knowledge base...")
        try:
            documents = prepare_knowledge_base(include_wikipedia=False)
            if documents:
                print(f"[App Init] ✓ Prepared {len(documents)} documents")
            else:
                print("[App Init] ⚠ No documents prepared, will use empty KB")
        except Exception as e:
            print(f"[App Init] ⚠ Error preparing knowledge base: {e}")
    
    # Step 2: Build FAISS index
    if not index_path.exists() and kb_json_path.exists():
        print("[App Init] Building FAISS index...")
        try:
            model, index, docs = build_faiss_index()
            if model and index and docs:
                print(f"[App Init] ✓ Built FAISS index with {len(docs)} documents")
            else:
                print("[App Init] ⚠ Failed to build FAISS index")
        except Exception as e:
            print(f"[App Init] ⚠ Error building FAISS index: {e}")
    
    print("[App Init] Local KB setup complete.\n")
