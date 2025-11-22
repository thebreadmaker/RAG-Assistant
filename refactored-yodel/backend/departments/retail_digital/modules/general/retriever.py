import yaml
from pathlib import Path
from typing import List, Dict
from rank_bm25 import BM25Okapi
from core.vector_manager import VectorManager
from core.config import get_settings
from core.logger import logger

settings = get_settings()

class HybridRetriever:
    def __init__(self, department: str):
        logger.info(f"🔍 Initializing HybridRetriever for department: {department}")
        self.department = department
        self.vector_manager = VectorManager(department)
        self.config = self._load_config()
        logger.debug(f"   Config loaded: {self.config}")
        logger.info(f"✅ HybridRetriever initialized")
        
    def _load_config(self) -> Dict:
        config_path = Path(__file__).parent / "module.yaml"
        if config_path.exists():
            logger.debug(f"   Loading config from: {config_path}")
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        logger.debug(f"   No config file found, using defaults")
        return {}
    
    def retrieve(self, query: str) -> List[Dict]:
        """Retrieve relevant chunks using hybrid search"""
        logger.info(f"🔎 Retrieval started - Query: '{query}'")
        
        top_k = self.config.get("top_k", settings.top_k)
        threshold = self.config.get("similarity_threshold", settings.similarity_threshold)
        logger.debug(f"   Parameters: top_k={top_k}, threshold={threshold}")
        
        # 1. Semantic search
        logger.debug(f"   🔸 Semantic search (top_k={top_k * 2})...")
        semantic_results = self.vector_manager.query(query, top_k=top_k * 2)
        logger.debug(f"   Semantic results before filter: {len(semantic_results)} chunks")
        
        # Filter by threshold
        semantic_results = [r for r in semantic_results if r["score"] >= threshold]
        logger.info(f"   ✅ Semantic search: {len(semantic_results)} chunks above threshold")
        
        avg_semantic_score = self._avg_score(semantic_results)
        logger.debug(f"   Average semantic score: {avg_semantic_score:.3f}")
        
        # 2. If results are poor, use BM25 fallback
        if not semantic_results or avg_semantic_score < threshold:
            logger.debug(f"   ⚠️ Semantic results insufficient, using BM25 fallback...")
            semantic_results = self._hybrid_search(query, semantic_results, top_k)
        
        # 3. Return top-k
        final_results = semantic_results[:top_k]
        logger.info(f"✅ Retrieval complete: {len(final_results)} chunks returned")
        
        for i, result in enumerate(final_results[:3]):
            logger.debug(f"   Result {i+1}: Score={result.get('score', 'N/A'):.3f}, Source={result.get('metadata', {}).get('source', 'unknown')}")
        
        return final_results
    
    def _avg_score(self, results: List[Dict]) -> float:
        if not results:
            return 0.0
        return sum(r["score"] for r in results) / len(results)
    
    def _hybrid_search(self, query: str, semantic_results: List[Dict], top_k: int) -> List[Dict]:
        """Combine semantic + BM25 using RRF"""
        logger.debug(f"   🔸 Hybrid search initiated (BM25 + RRF fusion)...")
        
        # Get all documents for BM25
        collection = self.vector_manager.get_or_create_collection()
        all_docs = collection.get()
        logger.debug(f"   Total documents in collection: {len(all_docs['documents'])}")
        
        if not all_docs["documents"]:
            logger.warning(f"   ⚠️ No documents found in collection, returning semantic results")
            return semantic_results
        
        # Tokenize for BM25
        tokenized_docs = [doc.lower().split() for doc in all_docs["documents"]]
        bm25 = BM25Okapi(tokenized_docs)
        logger.debug(f"   BM25 model trained on {len(tokenized_docs)} documents")
        
        # BM25 search
        query_tokens = query.lower().split()
        logger.debug(f"   Query tokens: {query_tokens}")
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
        logger.info(f"   ✅ BM25 search: {len(bm25_results)} results")
        
        # RRF fusion
        logger.debug(f"   🔸 RRF fusion: {len(semantic_results)} semantic + {len(bm25_results)} BM25...")
        fused = self._rrf_fusion(semantic_results, bm25_results)
        logger.info(f"   ✅ RRF fusion complete: {len(fused)} fused results")
        
        return fused[:top_k]
    
    def _rrf_fusion(self, semantic: List[Dict], bm25: List[Dict], k: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion with proper scoring"""
        logger.debug(f"Starting RRF fusion (k={k})")
        
        # Create doc ID → full document mapping
        all_docs = {}
        for doc in semantic + bm25:
            doc_id = doc["text"][:100]
            if doc_id not in all_docs:
                all_docs[doc_id] = doc
        
        scores = {}
        
        # Semantic scores (weight: 0.7)
        for rank, result in enumerate(semantic):
            doc_id = result["text"][:100]
            rrf_score = 0.7 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            logger.debug(f"Semantic rank {rank}: doc {doc_id[:30]}... → RRF score: {rrf_score:.4f}")
        
        logger.debug(f"RRF: Added {len(semantic)} semantic scores (weight=0.7)")
        
        # BM25 scores (weight: 0.3)
        for rank, result in enumerate(bm25):
            doc_id = result["text"][:100]
            rrf_score = 0.3 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            logger.debug(f"BM25 rank {rank}: doc {doc_id[:30]}... → RRF score: {rrf_score:.4f}")
        
        logger.debug(f"RRF: Added {len(bm25)} BM25 scores (weight=0.3)")
        
        # Sort by final RRF score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build result list with proper scores
        fused = []
        for doc_id, final_score in sorted_docs:
            if doc_id in all_docs:
                doc = all_docs[doc_id].copy()
                doc["score"] = final_score  # Use RRF score
                doc["rrf_rank"] = len(fused) + 1
                fused.append(doc)
                logger.debug(f"Final doc: {doc_id[:30]}... → score: {final_score:.4f}")
        
        logger.debug(f"RRF: Produced {len(fused)} fused results")
        return fused

retriever = HybridRetriever("retail_digital")