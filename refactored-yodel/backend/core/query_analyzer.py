"""
Query Analysis - Detect synthesis queries and extract entities
"""
import re
from typing import Dict, List
from core.logger import logger

from fuzzywuzzy import fuzz
from textblob import TextBlob

class QueryAnalyzer:
    def analyze(self, query: str) -> Dict:
        """Analyze query to determine retrieval strategy"""
        
        # Step 1: Correct spelling errors
        corrected_query, spell_confidence = self.correct_spelling(query)
        if corrected_query != query and spell_confidence > 0.85:
            logger.debug(f"Query corrected due to spelling: '{query}' → '{corrected_query}'")
            query = corrected_query
        
        # Extract customer IDs
        customer_ids = self._extract_customer_ids(query)
                
        # Detect synthesis intent
        is_synthesis = self._detect_synthesis_intent(query, customer_ids)
        
        # Extract topics
        topics = self._extract_topics(query)
        
        analysis = {
            "customer_ids": customer_ids,
            # "loan_ids": loan_ids,
            "requires_synthesis": is_synthesis,
            "topics": topics,
            "query_type": self._classify_query_type(query, customer_ids, is_synthesis)
        }
        
        logger.debug(f"Query analysis: {analysis}")
        return analysis
    
    def _extract_customer_ids(self, query: str) -> List[str]:
        """Extract customer IDs (6+ digits)"""
        return re.findall(r'\b\d{6,}\b', query)
    
    def _extract_loan_ids(self, query: str) -> List[str]:
        """Extract loan IDs (pattern: ABC-123)"""
        return re.findall(r'[A-Z]{3}-\d{3}', query)
    
    def _detect_synthesis_intent(self, query: str, customer_ids: List[str]) -> bool:
        """Detect if query needs cross-document reasoning"""
        query_lower = query.lower()
        
        # Synthesis indicators
        synthesis_patterns = [
            "what happens",
            "what will happen",
            "what action",
            "what should",
            "given",
            "for this",
            "with this",
            "based on"
        ]
        
        # Has customer ID + asks about consequences
        if customer_ids and any(pattern in query_lower for pattern in synthesis_patterns):
            return True
        
        # Asks about specific customer situation
        if customer_ids and any(word in query_lower for word in ["excluded", "declined", "why", "reason"]):
            return True
        
        return False
    
    def _extract_topics(self, query: str) -> List[str]:
        """Extract relevant topics from query"""
        topics = []
        query_lower = query.lower()
        
        topic_keywords = {
            "arrears": ["arrears", "overdue", "late", "dpd"],
            "eligibility": ["eligible", "qualify", "excluded", "declined"],
            "fees": ["fee", "charge", "cost", "interest"],
            "limits": ["limit", "amount", "maximum", "minimum"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in query_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _classify_query_type(self, query: str, customer_ids: List[str], is_synthesis: bool) -> str:
        """Classify query type for routing"""
        if is_synthesis:
            return "synthesis"
        elif customer_ids:
            return "customer_lookup"
        else:
            return "general"
    

    def correct_spelling(self, text: str) -> tuple[str, float]:
        """
        Correct spelling errors using TextBlob and return corrected text with confidence.
        Returns: (corrected_text, confidence_score)
        """
        try:
            blob = TextBlob(text)
            corrected = str(blob.correct())
            
            # Calculate confidence: how different is corrected from original?
            similarity = fuzz.ratio(text.lower(), corrected.lower())
            confidence = similarity / 100.0
            
            logger.debug(f"Spelling correction: '{text}' → '{corrected}' (confidence: {confidence:.2f})")
            
            return corrected, confidence
        except Exception as e:
            logger.debug(f"Spelling correction failed: {e}")
            return text, 1.0
    
    def find_similar_customer_id(self, customer_id: str, known_ids: List[str]) -> tuple[str, float]:
        """
        Find similar customer ID using fuzzy matching if exact match not found.
        Returns: (best_match_id, confidence_score)
        """
        best_match = None
        best_score = 0.0
        
        for known_id in known_ids:
            score = fuzz.ratio(customer_id, known_id)
            if score > best_score:
                best_score = score
                best_match = known_id
        
        confidence = best_score / 100.0
        logger.debug(f"Fuzzy match for '{customer_id}': '{best_match}' (confidence: {confidence:.2f})")
        
        return best_match, confidence
# Singleton
analyzer = QueryAnalyzer()