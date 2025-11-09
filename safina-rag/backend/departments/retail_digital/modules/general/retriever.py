import yaml
from pathlib import Path
from typing import List, Dict
from rank_bm25 import BM25Okapi
from core.vector_manager import VectorManager
from core.config import get_settings

settings = get_settings()

class HybridRetriever:
    def __init__(self, department: str):
        self.department = department
        self.vector_manager = VectorManager(department)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        config_path = Path(__file__).parent / "module.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def retrieve(self, query: str) -> List[Dict]:
        """Retrieve relevant chunks using hybrid search"""
        top_k = self.config.get("top_k", settings.top_k)
        threshold = self.config.get("similarity_threshold", settings.similarity_threshold)
        
        # 1. Semantic search
        semantic_results = self.vector_manager.query(query, top_k=top_k * 2)
        
        # Filter by threshold
        semantic_results = [r for r in semantic_results if r["score"] >= threshold]
        
        # 2. If results are poor, use BM25 fallback
        if not semantic_results or self._avg_score(semantic_results) < threshold:
            semantic_results = self._hybrid_search(query, semantic_results, top_k)
        
        # 3. Return top-k
        return semantic_results[:top_k]
    
    def _avg_score(self, results: List[Dict]) -> float:
        if not results:
            return 0.0
        return sum(r["score"] for r in results) / len(results)
    
    def _hybrid_search(self, query: str, semantic_results: List[Dict], top_k: int) -> List[Dict]:
        """Combine semantic + BM25 using RRF"""
        # Get all documents for BM25
        collection = self.vector_manager.get_or_create_collection()
        all_docs = collection.get()
        
        if not all_docs["documents"]:
            return semantic_results
        
        # Tokenize for BM25
        tokenized_docs = [doc.lower().split() for doc in all_docs["documents"]]
        bm25 = BM25Okapi(tokenized_docs)
        
        # BM25 search
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Get top BM25 results
        bm25_results = []
        for idx, score in enumerate(bm25_scores):
            if score > 0:
                bm25_results.append({
                    "text": all_docs["documents"][idx],
                    "metadata": all_docs["metadatas"][idx],
                    "score": score,
                    "bm25_rank": idx
                })
        
        bm25_results = sorted(bm25_results, key=lambda x: x["score"], reverse=True)[:top_k]
        
        # RRF fusion
        fused = self._rrf_fusion(semantic_results, bm25_results)
        
        return fused[:top_k]
    
    def _rrf_fusion(self, semantic: List[Dict], bm25: List[Dict], k: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion"""
        scores = {}
        
        # Semantic scores (weight: 0.7)
        for rank, result in enumerate(semantic):
            doc_id = result["text"][:100]  # Use text prefix as ID
            scores[doc_id] = scores.get(doc_id, 0) + 0.7 / (k + rank + 1)
        
        # BM25 scores (weight: 0.3)
        for rank, result in enumerate(bm25):
            doc_id = result["text"][:100]
            scores[doc_id] = scores.get(doc_id, 0) + 0.3 / (k + rank + 1)
        
        # Create unified results
        all_results = {r["text"][:100]: r for r in semantic + bm25}
        
        fused = []
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if doc_id in all_results:
                result = all_results[doc_id].copy()
                result["score"] = score
                fused.append(result)
        
        return fused

retriever = HybridRetriever("retail_digital")