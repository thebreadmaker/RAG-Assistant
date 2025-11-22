import requests
import time
from typing import List, Dict
from core.config import get_settings
from core.logger import logger
from departments.retail_digital.modules.general.prompts import build_rag_prompt

settings = get_settings()

class RAGGenerator:
    def __init__(self):
        logger.info(f"🤖 Initializing RAGGenerator")
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.model = settings.ollama_model
        logger.info(f"   Ollama URL: {self.ollama_url}")
        logger.info(f"   Model: {self.model}")
        logger.info(f"✅ RAGGenerator initialized")
    
    def generate(self, query: str, retrieved_chunks: List[Dict]) -> Dict:
        """Generate answer from retrieved context"""
        logger.info(f"📝 RAG generation started")
        logger.debug(f"   Query: '{query}'")
        logger.debug(f"   Retrieved chunks: {len(retrieved_chunks)}")
        
        if not retrieved_chunks:
            logger.warning(f"   ⚠️ No chunks provided, returning fallback response")
            return {
                "answer": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about specific policies.",
                "sources": [],
                "confidence": "low"
            }
        
        # Limit context to top 3 chunks, max 300 chars each
        top_chunks = retrieved_chunks[:3]
        trimmed_chunks = []
        for chunk in top_chunks:
            text = chunk["text"]
            if len(text) > 300:
                text = text[:300] + "..."
            trimmed_chunks.append({
                "text": text,
                "metadata": chunk["metadata"],
                "score": chunk["score"]
            })
        
        logger.debug(f"Using {len(trimmed_chunks)} chunks, avg length: {sum(len(c['text']) for c in trimmed_chunks) / len(trimmed_chunks):.0f} chars")
        
        # Build prompt with trimmed chunks
        prompt = build_rag_prompt(query, trimmed_chunks)
        logger.debug(f"Prompt length: {len(prompt)} chars (trimmed)")
        
        # Build prompt with context
        logger.debug(f"   Building prompt with {len(retrieved_chunks)} chunks...")
        prompt = build_rag_prompt(query, retrieved_chunks)
        logger.debug(f"   Prompt length: {len(prompt)} chars")
        
        try:
            logger.debug(f"   Calling LLM endpoint...")
            response = self._call_llm(prompt)
            logger.debug(f"   LLM response length: {len(response)} chars")
            
            answer = self._clean_response(response)
            logger.debug(f"   Cleaned response: {answer[:150]}..." if len(answer) > 150 else f"   Cleaned response: {answer}")
            
            # Extract sources
            sources = list(set([
                chunk["metadata"].get("source", "unknown") 
                for chunk in retrieved_chunks[:3]
            ]))
            logger.debug(f"   Sources: {sources}")
            
            # Calculate confidence
            avg_score = sum(c["score"] for c in retrieved_chunks) / len(retrieved_chunks)
            confidence = "high" if avg_score > 0.7 else "medium" if avg_score > 0.5 else "low"
            logger.info(f"   Avg chunk score: {avg_score:.3f} → Confidence: {confidence}")
            
            logger.info(f"✅ RAG generation successful")
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "num_chunks": len(retrieved_chunks)
            }
            
        except Exception as e:
            logger.error(f"❌ RAG generation failed: {str(e)}", exc_info=True)
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "confidence": "low"
            }
    
    def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM endpoint with logging"""
        logger.debug(f"   🔴 LLM call: POST {self.ollama_url}")
        start_time = time.time()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.7,
                "num_predict": 300,  # REDUCED from 512
                "repeat_penalty": 1.1
            }
        }
        
        logger.debug(f"      Payload: model={payload['model']}, temp={payload['options']['temperature']}")

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            duration = time.time() - start_time
            
            logger.debug(f"      Status: {response.status_code} - Duration: {duration:.2f}s")
            response.raise_for_status()
            
            result = response.json().get('response', '')
            logger.info(f"   ✅ LLM call succeeded ({duration:.2f}s)")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"   ❌ LLM call timeout (120s exceeded)")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"   ❌ LLM connection error: {str(e)}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"   ❌ LLM call failed after {duration:.2f}s: {str(e)}")
            raise
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response"""
        logger.debug(f"   Cleaning response...")
        # Remove LLM artifacts
        response = response.strip()
        response = response.replace("Assistant:", "").strip()
        response = response.replace("Answer:", "").strip()
        logger.debug(f"   Response cleaned")
        return response

generator = RAGGenerator()