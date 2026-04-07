"""
LLM Client for AI Engine
Same implementation as backend
"""

import httpx
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama LLM client"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        
    async def generate(self, prompt: str, system: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text completion"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or settings.OLLAMA_TEMPERATURE,
                    "num_predict": max_tokens or settings.OLLAMA_NUM_PREDICT,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "top_p": settings.OLLAMA_TOP_P,
                    "top_k": settings.OLLAMA_TOP_K,
                }
            }
            
            if system:
                payload["system"] = system
            
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            except httpx.HTTPError as e:
                logger.error(f"Ollama API error: {e}")
                raise
    
    async def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Chat completion"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature or settings.OLLAMA_TEMPERATURE,
                    "num_predict": max_tokens or settings.OLLAMA_NUM_PREDICT,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "top_p": settings.OLLAMA_TOP_P,
                    "top_k": settings.OLLAMA_TOP_K,
                }
            }
            
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
            except httpx.HTTPError as e:
                logger.error(f"Ollama chat API error: {e}")
                raise
    
    async def embeddings(self, text: str) -> List[float]:
        """Generate embeddings"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            
            try:
                response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
            except httpx.HTTPError as e:
                logger.error(f"Ollama embeddings API error: {e}")
                raise


class OpenAIClient:
    """OpenAI client (fallback)"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1"
    
    async def generate(self, prompt: str, system: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages, temperature, max_tokens)
    
    async def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Chat completion"""
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or settings.OPENAI_TEMPERATURE,
                "max_tokens": max_tokens or settings.OPENAI_MAX_TOKENS,
            }
            
            try:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                logger.error(f"OpenAI API error: {e}")
                raise
    
    async def embeddings(self, text: str) -> List[float]:
        """Generate embeddings"""
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "text-embedding-ada-002",
                "input": text
            }
            
            try:
                response = await client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
            except httpx.HTTPError as e:
                logger.error(f"OpenAI embeddings API error: {e}")
                raise


class LLMClient:
    """Unified LLM client"""
    
    def __init__(self):
        if settings.LLM_PROVIDER == "ollama":
            self.client = OllamaClient()
            logger.info(f"Using Ollama with model: {settings.OLLAMA_MODEL}")
        elif settings.LLM_PROVIDER == "openai":
            self.client = OpenAIClient()
            logger.info(f"Using OpenAI with model: {settings.OPENAI_MODEL}")
        else:
            raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
    
    async def generate(self, prompt: str, system: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Generate text completion"""
        return await self.client.generate(prompt, system, temperature, max_tokens)
    
    async def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Chat completion"""
        return await self.client.chat(messages, temperature, max_tokens)
    
    async def embeddings(self, text: str) -> List[float]:
        """Generate embeddings"""
        return await self.client.embeddings(text)


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
