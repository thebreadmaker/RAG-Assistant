import re
from typing import Optional, Dict
from sentence_transformers import SentenceTransformer
from core.config import get_settings

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
        tag = self._extract_tag(query)
        customer_id = self._extract_customer_id(query)
        
        # If customer ID found, it's definitely customer-specific
        if customer_id:
            query_type = "customer_specific"
        else:
            # Use semantic classification
            query_type = self._classify_intent(query)
        
        department = self.DEPARTMENTS.get(tag, "retail_digital")
        
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
        
        for intent, prototype_embeddings in self._intent_embeddings.items():
            # Compute similarity with all prototypes for this intent
            from sentence_transformers import util
            similarities = util.cos_sim(query_embedding, prototype_embeddings)
            max_sim = similarities.max().item()
            
            if max_sim > best_score:
                best_score = max_sim
                best_intent = intent
        
        # If similarity too low, default to general
        if best_score < 0.5:
            return "general"
        
        return best_intent
    
    def _extract_tag(self, query: str) -> Optional[str]:
        match = re.search(r'@\w+', query)
        return match.group(0) if match else None
    
    def _extract_customer_id(self, query: str) -> Optional[str]:
        match = re.search(r'\b\d{6,}\b', query)
        return match.group(0) if match else None

router = QueryRouter()