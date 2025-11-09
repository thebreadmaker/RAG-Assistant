#!/usr/bin/env python3
"""
Setup script for RAG system - Run this once after installing dependencies
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🚀 Setting up NCBA Safina RAG System...")
    
    # 1. Create necessary directories
    print("\n📁 Creating directory structure...")
    memory_dir = Path(__file__).parent / "departments" / "retail_digital" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created: {memory_dir}")
    
    db_dir = Path(__file__).parent / "departments" / "retail_digital" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created: {db_dir}")
    
    # 2. Download embedding model (first time only)
    print("\n📥 Downloading embedding model (this may take a minute)...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Embedding model ready")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return
    
    # 3. Ingest documents
    print("\n📚 Ingesting documents from memory folder...")
    try:
        from departments.retail_digital.modules.general.ingester import ingester
        ingester.ingest_all()
        
        from core.vector_manager import VectorManager
        vm = VectorManager("retail_digital")
        count = vm.count()
        print(f"✅ Ingested {count} document chunks")
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return
    
    # 4. Verify setup
    print("\n🔍 Verifying setup...")
    try:
        from departments.retail_digital.modules.general.retriever import retriever
        test_results = retriever.retrieve("What is LFA?")
        print(f"✅ Retrieval system working ({len(test_results)} results)")
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        return
    
    print("\n✨ Setup complete! You can now start the server:")
    print("   cd backend")
    print("   python -m uvicorn api.main:app --reload")

if __name__ == "__main__":
    main()