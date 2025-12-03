from typing import Optional, Dict, Any, List
import httpx
from server.config import settings
import json

class ModelRouter:
    """Router for managing different AI models with multi-provider support"""
    
    AVAILABLE_MODELS = {
        "openai/gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "provider": "openai",
            "api_model": "gpt-4-turbo",
            "context": 128000
        },
        "openai/gpt-4o": {
            "name": "GPT-4o",
            "provider": "openai",
            "api_model": "gpt-4o",
            "context": 128000
        },
        "openai/gpt-4.1-mini": {
            "name": "GPT-4.1 Mini",
            "provider": "openai",
            "api_model": "gpt-4o-mini",
            "context": 128000
        },
        "anthropic/claude-sonnet-4": {
            "name": "Claude Sonnet 4",
            "provider": "anthropic",
            "api_model": "claude-sonnet-4-20250514",
            "context": 200000
        },
        "anthropic/claude-3.5-sonnet": {
            "name": "Claude 3.5 Sonnet",
            "provider": "anthropic",
            "api_model": "claude-3-5-sonnet-20241022",
            "context": 200000
        },
        "anthropic/claude-3-opus": {
            "name": "Claude 3 Opus",
            "provider": "anthropic",
            "api_model": "claude-3-opus-20240229",
            "context": 200000
        },
        "google/gemini-pro-1.5": {
            "name": "Gemini Pro 1.5",
            "provider": "google",
            "api_model": "gemini-1.5-pro",
            "context": 1000000
        },
        "meta-llama/llama-3-70b-instruct": {
            "name": "Llama 3 70B",
            "provider": "openrouter",
            "api_model": "meta-llama/llama-3-70b-instruct",
            "context": 8192
        },
        "meta-llama/llama-3.1-405b-instruct": {
            "name": "Llama 3.1 405B",
            "provider": "openrouter",
            "api_model": "meta-llama/llama-3.1-405b-instruct",
            "context": 128000
        },
        "mistralai/mistral-large": {
            "name": "Mistral Large",
            "provider": "openrouter",
            "api_model": "mistralai/mistral-large",
            "context": 128000
        },
        "ollama": {
            "name": "Ollama (Local)",
            "provider": "ollama",
            "api_model": "llama3.2",
            "context": 8192
        },
        "custom": {
            "name": "Custom Model",
            "provider": "custom",
            "api_model": "custom",
            "context": 4096
        }
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.request_count = 0
        self.error_count = 0
        self.last_error = None
        
    def _get_provider_for_model(self, model_name: str) -> str:
        """Determine the provider for a model. Always tries direct API keys first, but falls back to OpenRouter."""
        # Check if model explicitly maps to a provider
        if model_name in self.AVAILABLE_MODELS:
            preferred_provider = self.AVAILABLE_MODELS[model_name]["provider"]
            
            # Check for Ollama first (local, no API key needed)
            if preferred_provider == "ollama":
                return "ollama"
            
            # Check for custom model
            if preferred_provider == "custom":
                return "custom"
            
            # Try direct API if available
            if preferred_provider == "anthropic" and settings.ANTHROPIC_API_KEY:
                return "anthropic"
            elif preferred_provider == "openai" and settings.OPENAI_API_KEY:
                return "openai"
            elif preferred_provider == "google" and settings.GOOGLE_API_KEY:
                return "google"
            # Otherwise use OpenRouter for any model
            elif settings.OPENROUTER_API_KEY:
                return "openrouter"
        
        # Check for Ollama models by prefix
        if model_name.startswith("ollama/") or model_name == "ollama":
            return "ollama"
        
        # For unknown models, try by prefix
        if (model_name.startswith("anthropic/") or model_name.startswith("claude")) and settings.ANTHROPIC_API_KEY:
            return "anthropic"
        if (model_name.startswith("openai/") or model_name.startswith("gpt")) and settings.OPENAI_API_KEY:
            return "openai"
        if (model_name.startswith("google/") or model_name.startswith("gemini")) and settings.GOOGLE_API_KEY:
            return "google"
        
        # Default to OpenRouter for any model
        if settings.OPENROUTER_API_KEY:
            return "openrouter"
        
        raise Exception("OpenRouter API key is required. Please add OPENROUTER_API_KEY to your environment.")
        
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return [
            {"id": k, **v} 
            for k, v in self.AVAILABLE_MODELS.items()
        ]
    
    async def generate(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate response from specified model using the best available provider"""
        
        provider = self._get_provider_for_model(model_name)
        
        print(f"[ModelRouter] Using provider '{provider}' for model '{model_name}'")
        
        if provider == "anthropic":
            return await self._generate_anthropic(model_name, system_prompt, user_message, context)
        elif provider == "openai":
            return await self._generate_openai(model_name, system_prompt, user_message, context)
        elif provider == "google":
            return await self._generate_google(model_name, system_prompt, user_message, context)
        elif provider == "ollama":
            return await self._generate_ollama(model_name, system_prompt, user_message, context)
        elif provider == "custom":
            return await self._generate_custom(system_prompt, user_message, context)
        else:
            return await self._generate_openrouter(model_name, system_prompt, user_message, context)
    
    async def _generate_anthropic(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using Anthropic API directly"""
        
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise Exception("Anthropic API key is not configured")
        
        api_model = "claude-3-5-sonnet-20241022"
        if model_name in self.AVAILABLE_MODELS:
            api_model = self.AVAILABLE_MODELS[model_name].get("api_model", api_model)
        elif "opus" in model_name.lower():
            api_model = "claude-3-opus-20240229"
        elif "sonnet" in model_name.lower():
            if "3.5" in model_name or "3-5" in model_name:
                api_model = "claude-3-5-sonnet-20241022"
            else:
                api_model = "claude-3-sonnet-20240229"
        
        messages = []
        if context:
            for msg in context:
                role = msg.get("role", "user")
                if role == "system":
                    continue
                messages.append({
                    "role": role,
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            self.request_count += 1
            print(f"[Anthropic] Request #{self.request_count} to model: {api_model}")
            
            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": api_model,
                    "max_tokens": 2048,
                    "system": system_prompt,
                    "messages": messages
                },
                timeout=120.0
            )
            
            if response.status_code != 200:
                self.error_count += 1
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_message = response.text[:200]
                
                self.last_error = f"Anthropic API {response.status_code}: {error_message}"
                raise Exception(self.last_error)
            
            data = response.json()
            content = data.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "").strip()
            
            raise Exception("Empty response from Anthropic")
            
        except httpx.TimeoutException:
            self.error_count += 1
            self.last_error = "Anthropic API timeout (120s)"
            raise Exception(self.last_error)
        except Exception as e:
            if "Anthropic" not in str(e):
                self.error_count += 1
                self.last_error = f"Anthropic error: {str(e)[:100]}"
            raise
    
    async def _generate_openai(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using OpenAI API directly"""
        
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise Exception("OpenAI API key is not configured")
        
        api_model = "gpt-4-turbo"
        if model_name in self.AVAILABLE_MODELS:
            api_model = self.AVAILABLE_MODELS[model_name].get("api_model", api_model)
        elif "gpt-4o" in model_name.lower():
            api_model = "gpt-4o"
        elif "gpt-4-turbo" in model_name.lower():
            api_model = "gpt-4-turbo"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            self.request_count += 1
            print(f"[OpenAI] Request #{self.request_count} to model: {api_model}")
            
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": api_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048
                },
                timeout=120.0
            )
            
            if response.status_code != 200:
                self.error_count += 1
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_message = response.text[:200]
                
                self.last_error = f"OpenAI API {response.status_code}: {error_message}"
                raise Exception(self.last_error)
            
            data = response.json()
            if "choices" not in data or len(data["choices"]) == 0:
                raise Exception("Invalid response structure from OpenAI")
            
            content = data["choices"][0]["message"]["content"].strip()
            if not content:
                raise Exception("Empty response from OpenAI")
            
            return content
            
        except httpx.TimeoutException:
            self.error_count += 1
            self.last_error = "OpenAI API timeout (120s)"
            raise Exception(self.last_error)
        except Exception as e:
            if "OpenAI" not in str(e):
                self.error_count += 1
                self.last_error = f"OpenAI error: {str(e)[:100]}"
            raise
    
    async def _generate_google(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using Google Gemini API directly"""
        
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return await self._generate_openrouter(model_name, system_prompt, user_message, context)
        
        api_model = "gemini-1.5-pro"
        if model_name in self.AVAILABLE_MODELS:
            api_model = self.AVAILABLE_MODELS[model_name].get("api_model", api_model)
        
        contents = []
        
        full_prompt = f"{system_prompt}\n\n{user_message}"
        if context:
            for msg in context:
                role = "user" if msg.get("role") in ["user", "system"] else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        contents.append({
            "role": "user",
            "parts": [{"text": full_prompt}]
        })
        
        try:
            self.request_count += 1
            print(f"[Google] Request #{self.request_count} to model: {api_model}")
            
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 4096
                    }
                },
                timeout=120.0
            )
            
            if response.status_code != 200:
                self.error_count += 1
                self.last_error = f"Google API {response.status_code}: {response.text[:200]}"
                raise Exception(self.last_error)
            
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates and len(candidates) > 0:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and len(parts) > 0:
                    return parts[0].get("text", "").strip()
            
            raise Exception("Empty response from Google")
            
        except Exception as e:
            if "Google" not in str(e):
                self.error_count += 1
                self.last_error = f"Google error: {str(e)[:100]}"
            raise
    
    async def _generate_openrouter(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using OpenRouter API"""
        
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            raise Exception("OpenRouter API key is not configured. Please add OPENROUTER_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY to your environment.")
        
        if not api_key.startswith("sk-"):
            raise Exception("OpenRouter API key format is invalid (should start with 'sk-')")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            self.request_count += 1
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/performa-ai",
                "X-Title": "Performa Autonomous Agent",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }
            
            print(f"[OpenRouter] Request #{self.request_count} to model: {model_name}")
            
            response = await self.client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120.0
            )
            
            data = response.json()
            
            if response.status_code != 200:
                error_data = data if isinstance(data, dict) else {}
                error_obj = error_data.get("error", {})
                error_message = error_obj.get("message", "") if isinstance(error_obj, dict) else str(error_obj)
                error_code = error_obj.get("code", "") if isinstance(error_obj, dict) else ""
                
                print(f"[OpenRouter] Status {response.status_code}: {error_message}")
                
                if response.status_code >= 500:
                    self.error_count += 1
                    error_msg = f"OpenRouter server error {response.status_code}"
                    self.last_error = error_msg
                    raise Exception(error_msg)
                elif response.status_code == 429:
                    self.error_count += 1
                    error_msg = f"Rate limited - wait before retrying"
                    self.last_error = error_msg
                    raise Exception(error_msg)
                elif response.status_code == 401:
                    self.error_count += 1
                    error_msg = f"Invalid API key"
                    self.last_error = error_msg
                    raise Exception(error_msg)
                elif response.status_code == 402:
                    if "insufficient" in error_message.lower() or "credit" in error_message.lower() or "balance" in error_message.lower():
                        self.error_count += 1
                        error_msg = f"Insufficient credits: {error_message}"
                        self.last_error = error_msg
                        raise Exception(error_msg)
                    else:
                        print(f"[OpenRouter] 402 but not credit issue, retrying...")
                        self.error_count += 1
                        error_msg = f"Payment issue: {error_message}"
                        self.last_error = error_msg
                        raise Exception(error_msg)
                else:
                    self.error_count += 1
                    error_msg = f"API {response.status_code}: {error_message}"
                    self.last_error = error_msg
                    raise Exception(error_msg)
            
            if "choices" not in data or len(data["choices"]) == 0:
                if "error" in data:
                    error_obj = data.get("error", {})
                    error_message = error_obj.get("message", str(error_obj)) if isinstance(error_obj, dict) else str(error_obj)
                    raise Exception(f"API error: {error_message}")
                raise Exception("Invalid response structure from OpenRouter")
            
            content = data["choices"][0]["message"]["content"]
            if content:
                content = content.strip()
            
            if not content:
                raise Exception("Empty response from OpenRouter")
            
            return content
            
        except httpx.TimeoutException:
            self.error_count += 1
            error_msg = "OpenRouter API timeout (120s)"
            self.last_error = error_msg
            raise Exception(error_msg)
        except httpx.ConnectError:
            self.error_count += 1
            error_msg = "No internet connection or cannot reach OpenRouter API"
            self.last_error = error_msg
            raise Exception(error_msg)
        except Exception as e:
            self.error_count += 1
            error_msg = f"System error: {type(e).__name__}: {str(e)[:100]}"
            self.last_error = error_msg
            raise
    
    async def _generate_ollama(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using local Ollama command line (ollama run)"""
        from .ollama_local import ollama_client
        
        api_model = model_name
        if model_name in self.AVAILABLE_MODELS:
            api_model = self.AVAILABLE_MODELS[model_name].get("api_model", "llama3.2")
        elif model_name.startswith("ollama/"):
            api_model = model_name[7:]
        
        try:
            self.request_count += 1
            print(f"[Ollama] Request #{self.request_count} to model: {api_model} (using local command)")
            
            response = await ollama_client.generate(
                model_name=api_model,
                system_prompt=system_prompt,
                user_message=user_message,
                context=context
            )
            
            if not response:
                raise Exception("Empty response from Ollama")
            
            return response.strip()
            
        except Exception as e:
            self.error_count += 1
            error_msg = str(e)
            if "not installed" in error_msg.lower():
                self.last_error = "Ollama is not installed. Install from https://ollama.ai"
            elif "timeout" in error_msg.lower():
                self.last_error = "Ollama timeout. Consider using a smaller model."
            else:
                self.last_error = f"Ollama error: {error_msg[:100]}"
            raise Exception(self.last_error)

    async def _generate_custom(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate using custom model endpoint"""
        
        if not settings.CUSTOM_MODEL_ENDPOINT:
            raise ValueError("Custom model endpoint not configured")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.post(
                settings.CUSTOM_MODEL_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.CUSTOM_MODEL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"messages": messages}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", data.get("content", ""))
        except Exception as e:
            raise Exception(f"Custom model error: {str(e)}")
    
    async def chat(self, message: str) -> str:
        """Simple chat interface - routes through configured provider"""
        # Use GPT-4 Turbo as default since we're routing through OpenRouter
        model = "openai/gpt-4-turbo"
        try:
            return await self.generate(
                model,
                "You are a helpful cyber security AI assistant.",
                message
            )
        except Exception as e:
            # Re-raise with better context
            error_str = str(e)
            if "OpenRouter" in error_str or "402" in error_str or "401" in error_str:
                raise Exception(error_str)  # OpenRouter errors are already detailed
            raise Exception(f"Chat generation failed: {error_str}")
    
    async def test_connection(self, provider: str, model: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to AI model using the appropriate provider"""
        import time
        
        provider_lower = provider.lower()
        
        if provider_lower == "anthropic":
            test_key = api_key or settings.ANTHROPIC_API_KEY
            if not test_key:
                return {
                    "status": "error",
                    "message": "Anthropic API key is not configured. Please add ANTHROPIC_API_KEY to your secrets.",
                    "provider": provider,
                    "model": model
                }
            
            try:
                start_time = time.time()
                
                response = await self.client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": test_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.AVAILABLE_MODELS.get(model, {}).get("api_model", "claude-3-5-sonnet-20241022"),
                        "max_tokens": 20,
                        "messages": [{"role": "user", "content": "Say 'API connection successful' in 5 words or less."}]
                    },
                    timeout=30.0
                )
                
                latency = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", [{}])[0].get("text", "")
                    return {
                        "status": "success",
                        "message": "API connection successful",
                        "provider": provider,
                        "model": model,
                        "latency": f"{latency}ms",
                        "response": content
                    }
                else:
                    error_data = response.json() if response.text else {}
                    return {
                        "status": "error",
                        "message": f"Anthropic API error {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        "provider": provider,
                        "model": model
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}",
                    "provider": provider,
                    "model": model
                }
        
        elif provider_lower == "openai":
            test_key = api_key or settings.OPENAI_API_KEY
            if not test_key:
                return {
                    "status": "error",
                    "message": "OpenAI API key is not configured. Please add OPENAI_API_KEY to your secrets.",
                    "provider": provider,
                    "model": model
                }
            
            try:
                start_time = time.time()
                
                response = await self.client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {test_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.AVAILABLE_MODELS.get(model, {}).get("api_model", "gpt-4-turbo"),
                        "messages": [{"role": "user", "content": "Say 'API connection successful' in 5 words or less."}],
                        "max_tokens": 20
                    },
                    timeout=30.0
                )
                
                latency = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "message": "API connection successful",
                        "provider": provider,
                        "model": model,
                        "latency": f"{latency}ms",
                        "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    }
                else:
                    error_data = response.json() if response.text else {}
                    return {
                        "status": "error",
                        "message": f"OpenAI API error {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        "provider": provider,
                        "model": model
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}",
                    "provider": provider,
                    "model": model
                }
        
        elif provider_lower == "ollama":
            from .ollama_local import ollama_client
            try:
                result = await ollama_client.test_connection(model)
                return {
                    "status": result.get("status", "error"),
                    "message": result.get("message", "Unknown"),
                    "provider": provider,
                    "model": model,
                    "available_models": result.get("available_models", [])
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Ollama error: {str(e)}",
                    "provider": provider,
                    "model": model
                }
        
        else:
            test_key = api_key or settings.OPENROUTER_API_KEY
            
            if not test_key or not test_key.strip():
                return {
                    "status": "error",
                    "message": "API key is not configured",
                    "provider": provider,
                    "model": model
                }
            
            if not test_key.startswith("sk-"):
                return {
                    "status": "error",
                    "message": "Invalid API key format (should start with 'sk-')",
                    "provider": provider,
                    "model": model
                }
            
            try:
                start_time = time.time()
                
                headers = {
                    "Authorization": f"Bearer {test_key}",
                    "HTTP-Referer": "https://github.com/performa-ai",
                    "X-Title": "Performa API Test",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Say 'API connection successful' in 5 words or less."}],
                    "max_tokens": 20
                }
                
                response = await self.client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                latency = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "message": "API connection successful",
                        "provider": provider,
                        "model": model,
                        "latency": f"{latency}ms",
                        "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    }
                elif response.status_code == 402:
                    return {
                        "status": "error",
                        "message": "Insufficient credits on OpenRouter account",
                        "provider": provider,
                        "model": model
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "message": "Invalid API key",
                        "provider": provider,
                        "model": model
                    }
                else:
                    error_data = response.json() if response.text else {}
                    return {
                        "status": "error",
                        "message": f"API error {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        "provider": provider,
                        "model": model
                    }
                    
            except httpx.TimeoutException:
                return {
                    "status": "error",
                    "message": "Connection timeout (30s)",
                    "provider": provider,
                    "model": model
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Connection error: {str(e)}",
                    "provider": provider,
                    "model": model
                }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
