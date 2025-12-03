# Custom model implementation
from typing import Dict, Any, List, Optional
import httpx
from server.config import settings

class CustomModelClient:
    """Client for custom AI model"""
    
    def __init__(self):
        self.endpoint = settings.CUSTOM_MODEL_ENDPOINT
        self.api_key = settings.CUSTOM_MODEL_API_KEY
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response from custom model"""
        
        payload = {
            "prompt": prompt,
            **kwargs
        }
        
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        response = await self.client.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Adjust based on your model's response format
        return data.get("response", data.get("text", ""))
    
    async def close(self):
        await self.client.aclose()
