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
            "why is customer 599741 excluded from LFA",
            "check eligibility for account 5997410016",
            "what are the failed checks for customer 599650",
            "why was customer ID 503446 declined",
            "show me customer 558473 arrears status"
        ],
        "general": [
            "what is the digital personal loan",
            "explain the LFA eligibility requirements",
            "how do I qualify for a loan",
            "what are the charges and fees",
            "tell me about the vacation policy",
            "what happens if I repay late"
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
        logger.debug(f"Router classifying query: '{query[:80]}...'")
        
        tag = self._extract_tag(query)
        customer_id = self._extract_customer_id(query)
        logger.debug(f"Tag extracted: {tag}")
        logger.debug(f"Customer ID extracted: {customer_id}")
        
        # NEW: Rule-based pre-classification
        query_lower = query.lower()
        
        # RULE 1: If customer ID found → customer_specific
        if customer_id:
            query_type = "customer_specific"
            logger.debug(f"Classification: customer_specific (ID found)")
        
        # RULE 2: If query asks "what is", "explain", "how to" → general
        elif any(phrase in query_lower for phrase in [
            "what is", "what are", "tell me about", "explain", 
            "how do i", "how can i", "what happens"
        ]):
            query_type = "general"
            logger.debug(f"Classification: general (question pattern)")
        
        # RULE 3: If query contains "customer", "account", "excluded" without ID → likely wants to ask about customer
        elif any(word in query_lower for word in ["customer", "account", "excluded", "declined"]) and not customer_id:
            # Use semantic only if ambiguous
            query_type = self._classify_intent(query)
            logger.debug(f"Classification: {query_type} (semantic - ambiguous)")
        
        # RULE 4: Default to semantic
        else:
            query_type = self._classify_intent(query)
            logger.debug(f"Classification: {query_type} (semantic)")
        
        department = self.DEPARTMENTS.get(tag, "retail_digital")
        logger.debug(f"Department: {department}")
        
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