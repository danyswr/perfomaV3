"""
OpenRouter Model Integration - Improved based on AIEngine reference
Handles communication with OpenRouter API with proper error handling and validation
"""
import requests
from typing import List, Dict, Any, Optional
from server.config import settings

class OpenRouterModel:
    """OpenRouter model client with enhanced error handling"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4.1-mini"):
        self.api_key = api_key.strip() if api_key else ""
        self.model = model
        self.request_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.api_key_valid = self._validate_api_key()

    def _validate_api_key(self) -> bool:
        """Validate API key format and presence"""
        if not self.api_key:
            self.last_error = "API key is empty"
            return False
        # OpenRouter API keys start with "sk-"
        if not self.api_key.startswith("sk-"):
            self.last_error = f"API key format invalid (got: {self.api_key[:10]}...)"
            return False
        return True

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate response from OpenRouter API
        Returns: 
        - Success: {"status": "success", "content": "response", "model": "model_used", "usage": {...}}
        - Error: {"status": "error", "message": "error details", "code": "error_code"}
        """
        if not self.api_key_valid:
            self.error_count += 1
            return {
                "status": "error",
                "message": f"API Key Error: {self.last_error}",
                "code": "INVALID_API_KEY"
            }

        # Clean messages
        clean_msgs = []
        for msg in messages:
            role = msg.get("role", "user").strip()
            content = str(msg.get("content", "")).strip()
            if content and role in ["user", "assistant", "system"]:
                clean_msgs.append({"role": role, "content": content})
        
        if not clean_msgs:
            return {
                "status": "error",
                "message": "No valid messages provided",
                "code": "NO_MESSAGES"
            }

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/performa-ai",
            "X-Title": "Performa Autonomous Agent",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": clean_msgs,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.95
        }

        try:
            self.request_count += 1
            print(f"[OpenRouter] Request #{self.request_count} to model: {self.model}")
            print(f"[OpenRouter] Messages: {len(clean_msgs)}, Max tokens: {max_tokens}")
            
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if resp.status_code != 200:
                self.error_count += 1
                error_data = {}
                try:
                    error_data = resp.json()
                except:
                    error_data = {"error": {"message": resp.text[:200]}}
                
                error_msg = error_data.get("error", {}).get("message", str(error_data))
                
                # Handle specific status codes
                if resp.status_code == 402:
                    self.last_error = "Insufficient credits on OpenRouter account"
                    code = "INSUFFICIENT_CREDITS"
                elif resp.status_code == 401:
                    self.last_error = "Invalid API key for OpenRouter"
                    code = "INVALID_AUTH"
                elif resp.status_code == 429:
                    self.last_error = "Rate limit exceeded on OpenRouter"
                    code = "RATE_LIMIT"
                elif resp.status_code == 500:
                    self.last_error = "OpenRouter service error"
                    code = "SERVICE_ERROR"
                else:
                    self.last_error = error_msg
                    code = f"HTTP_{resp.status_code}"
                
                print(f"[OpenRouter] Error {resp.status_code}: {self.last_error}")
                
                return {
                    "status": "error",
                    "message": f"API {resp.status_code}: {self.last_error}",
                    "code": code,
                    "raw_response": error_msg
                }
            
            response_data = resp.json()
            try:
                content = response_data["choices"][0]["message"]["content"].strip()
                usage = response_data.get("usage", {})
                
                print(f"[OpenRouter] Success! Tokens - In: {usage.get('prompt_tokens', 0)}, Out: {usage.get('completion_tokens', 0)}")
                
                return {
                    "status": "success",
                    "content": content,
                    "model": response_data.get("model", self.model),
                    "usage": usage
                }
            except (KeyError, IndexError) as e:
                self.error_count += 1
                print(f"[OpenRouter] Parse error: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Failed to parse API response: {str(e)}",
                    "code": "PARSE_ERROR"
                }
            
        except requests.exceptions.Timeout:
            self.error_count += 1
            self.last_error = "OpenRouter API request timed out (120s)"
            print(f"[OpenRouter] Timeout: {self.last_error}")
            return {
                "status": "error",
                "message": self.last_error,
                "code": "TIMEOUT"
            }
        except requests.exceptions.ConnectionError:
            self.error_count += 1
            self.last_error = "Cannot connect to OpenRouter API"
            print(f"[OpenRouter] Connection error: {self.last_error}")
            return {
                "status": "error",
                "message": self.last_error,
                "code": "CONNECTION_ERROR"
            }
        except Exception as e:
            self.error_count += 1
            self.last_error = f"Unexpected error: {str(e)}"
            print(f"[OpenRouter] Exception: {type(e).__name__}: {self.last_error}")
            return {
                "status": "error",
                "message": self.last_error,
                "code": "SYSTEM_ERROR"
            }

    def is_api_key_valid(self) -> bool:
        """Check API key validity"""
        return self.api_key_valid

    def get_error_info(self) -> Dict[str, Any]:
        """Get diagnostic error information"""
        return {
            "last_error": self.last_error,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": f"{(self.error_count / max(1, self.request_count)) * 100:.1f}%",
            "api_key_valid": self.api_key_valid,
            "model": self.model
        }
