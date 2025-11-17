import re
from typing import Optional, Dict
from sentence_transformers import SentenceTransformer
from core.config import get_settings
from core.logger import logger

settings = get_settings()

class QueryRouter:
    DEPARTMENTS = {
        "@retail_digital": "retail_digital"
    }
    
    # Intent prototypes for semantic matching
    INTENT_PROTOTYPES = {
        "customer_specific": [
            "check customer eligibility",
            "why is customer excluded",
            "customer loan status",
            "account arrears check"
        ],
        "general": [
            "what is the policy",
            "how does the process work",
            "explain the requirements",
            "what are the fees"
        ]
    }
    
    def __init__(self):
        self.embedder = None
        self._intent_embeddings = {}
    
    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = SentenceTransformer(settings.embedding_model)
            # Pre-compute intent prototype embeddings
            for intent, phrases in self.INTENT_PROTOTYPES.items():
                self._intent_embeddings[intent] = self.embedder.encode(
                    phrases, 
                    convert_to_tensor=True
                )
        return self.embedder
    
    def classify_query(self, query: str) -> Dict:
        logger.debug(f"   Router classifying query: '{query[:80]}...'") if len(query) > 80 else logger.debug(f"   Router classifying query: '{query}'")
        
        tag = self._extract_tag(query)
        customer_id = self._extract_customer_id(query)
        logger.debug(f"      Tag extracted: {tag}")
        logger.debug(f"      Customer ID extracted: {customer_id}")
        
        # If customer ID found, it's definitely customer-specific
        if customer_id:
            query_type = "customer_specific"
            logger.debug(f"      Classification: customer_specific (ID found)")
        else:
            # Use semantic classification
            query_type = self._classify_intent(query)
            logger.debug(f"      Classification: {query_type} (semantic)")
        
        department = self.DEPARTMENTS.get(tag, "retail_digital")
        logger.debug(f"      Department: {department}")
        
        return {
            "department": department,
            "type": query_type,
            "customer_id": customer_id,
            "original_query": query,
            "tag": tag
        }
    
    def _classify_intent(self, query: str) -> str:
        """Use semantic similarity to classify intent"""
        embedder = self._get_embedder()
        query_embedding = embedder.encode(query, convert_to_tensor=True)
        
        best_intent = "general"
        best_score = 0.0
        scores = {}
        
        for intent, prototype_embeddings in self._intent_embeddings.items():
            # Compute similarity with all prototypes for this intent
            from sentence_transformers import util
            similarities = util.cos_sim(query_embedding, prototype_embeddings)
            max_sim = similarities.max().item()
            scores[intent] = max_sim
            
            if max_sim > best_score:
                best_score = max_sim
                best_intent = intent
        
        logger.debug(f"         Semantic similarity scores: {scores}")
        logger.debug(f"         Best match: {best_intent} ({best_score:.3f})")
        
        # If similarity too low, default to general
        if best_score < 0.5:
            logger.debug(f"         Score below threshold (0.5), defaulting to general")
            return "general"
        
        return best_intent
    
    def _extract_tag(self, query: str) -> Optional[str]:
        match = re.search(r'@\w+', query)
        return match.group(0) if match else None
    
    def _extract_customer_id(self, query: str) -> Optional[str]:
        match = re.search(r'\b\d{6,}\b', query)
        return match.group(0) if match else None

router = QueryRouter()