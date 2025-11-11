"""
LLM Provider Interface - Abstraction layer for switching between Ollama and Poe Claude
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import requests
from core.config import get_settings

settings = get_settings()


class LLMInterface(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass


class OllamaLLM(LLMInterface):
    """Ollama LLM Provider"""
    
    def __init__(self):
        self.ollama_url = f"{settings.ollama_host}/api/generate"
        self.model = settings.ollama_model
    
    def generate(self, prompt: str, temperature: float = 0.3, 
                num_predict: int = 512, **kwargs) -> str:
        """Generate response using Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.7),
                "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
                "num_predict": num_predict,
                "stop": kwargs.get("stop", [])
            }
        }
        
        response = requests.post(self.ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        
        return response.json().get('response', '')


class PoeLLM(LLMInterface):
    """Poe Claude LLM Provider via OpenAI API"""
    
    def __init__(self):
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=settings.poe_api_key,
                base_url="https://api.poe.com/v1"
            )
            self.model = settings.poe_model
        except ImportError:
            raise ImportError("OpenAI library required for Poe. Install: pip install openai")
    
    def generate(self, prompt: str, temperature: float = 0.3, 
                max_tokens: int = 512, **kwargs) -> str:
        """Generate response using Poe Claude via OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=kwargs.get("top_p", 0.8)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Poe API error: {str(e)}")


def get_llm_client() -> LLMInterface:
    """
    Factory function to get LLM client based on configuration
    Reads LLM_PROVIDER from settings (set via .env)
    """
    provider = getattr(settings, 'llm_provider', 'ollama').lower()
    
    if provider == 'poe':
        return PoeLLM()
    elif provider == 'ollama':
        return OllamaLLM()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'ollama' or 'poe'")