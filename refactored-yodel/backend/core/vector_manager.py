import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from core.config import get_settings

settings = get_settings()

class VectorManager:
    def __init__(self, department: str):
        self.department = department
        self.db_path = Path(settings.vector_db_persist_dir) / department / "db"
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.embedder = SentenceTransformer(settings.embedding_model)
        self.collection_name = f"{department}_general"
        
    def get_or_create_collection(self):
        """Get or create the department's collection"""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"department": self.department}
        )
    
    def ingest(self, chunks: List[Dict]):
        """Insert document chunks into VectorDB"""
        if not chunks:
            return
        
        collection = self.get_or_create_collection()
        
        documents = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(documents).tolist()
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
    
    def query(
        self, 
        query_text: str, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Semantic search for relevant chunks"""
        collection = self.get_or_create_collection()
        
        query_embedding = self.embedder.encode(query_text).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters
        )
        
        # Format results
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "score": 1 - results["distances"][0][i]  # Convert to similarity
                })
        
        return chunks
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
    
    def count(self) -> int:
        """Get number of documents"""
        collection = self.get_or_create_collection()
        return collection.count()
    
    def verify_embeddings(self):
        """Test embedding generation and similarity"""
        test_texts = [
            "digital personal loan",
            "personal loan application",
            "unrelated concept"
        ]
        
        embeddings = self.embedder.encode(test_texts)
        
        # Check similarity
        from numpy.linalg import norm
        def cosine_sim(a, b):
            return (a @ b) / (norm(a) * norm(b))
        
        sim_1_2 = cosine_sim(embeddings[0], embeddings[1])
        sim_1_3 = cosine_sim(embeddings[0], embeddings[2])
        
        print(f"Similar texts similarity: {sim_1_2:.3f} (should be >0.6)")
        print(f"Different texts similarity: {sim_1_3:.3f} (should be <0.4)")
        
        if sim_1_2 < 0.5:
            raise ValueError("Embeddings not working correctly!")