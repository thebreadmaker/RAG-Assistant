import requests
from typing import List, Dict
from core.config import get_settings
from departments.retail_digital.modules.general.prompts import build_rag_prompt

settings = get_settings()

class RAGGenerator:
    def __init__(self):
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.model = settings.ollama_model
    
    def generate(self, query: str, retrieved_chunks: List[Dict]) -> Dict:
        """Generate answer from retrieved context"""
        if not retrieved_chunks:
            return {
                "answer": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about specific policies.",
                "sources": [],
                "confidence": "low"
            }
        
        # Build prompt with context
        prompt = build_rag_prompt(query, retrieved_chunks)
        
        try:
            response = self._call_llm(prompt)
            answer = self._clean_response(response)
            
            # Extract sources
            sources = list(set([
                chunk["metadata"].get("source", "unknown") 
                for chunk in retrieved_chunks[:3]
            ]))
            
            # Calculate confidence
            avg_score = sum(c["score"] for c in retrieved_chunks) / len(retrieved_chunks)
            confidence = "high" if avg_score > 0.7 else "medium" if avg_score > 0.5 else "low"
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "num_chunks": len(retrieved_chunks)
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "confidence": "low"
            }
    
    def _call_llm(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,     # Slightly warmer for natural tone
                "top_p": 0.7,           # Allows mild stylistic diversity
                "num_predict": 512,     # More space for graceful pacing
                "repeat_penalty": 1.1   # Softer phrasing, avoids stiffness
            }
        }

        response = requests.post(self.ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def _clean_response(self, response: str) -> str:
        # Remove LLM artifacts
        response = response.strip()
        response = response.replace("Assistant:", "").strip()
        response = response.replace("Answer:", "").strip()
        return response

generator = RAGGenerator()