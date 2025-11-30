import asyncio
import subprocess
import json
from typing import Optional, List, Dict, Any

class OllamaLocalClient:
    """Client for running Ollama models using local command line"""
    
    AVAILABLE_MODELS = [
        "llama3.2",
        "llama3.1",
        "llama3",
        "codellama",
        "mistral",
        "mixtral",
        "gemma2",
        "gemma",
        "phi3",
        "qwen2.5",
        "deepseek-coder",
        "neural-chat",
        "starling-lm",
    ]
    
    def __init__(self):
        self.default_model = "llama3.2"
        self.timeout = 180
        
    async def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed and available"""
        try:
            process = await asyncio.create_subprocess_exec(
                "which", "ollama",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return process.returncode == 0 and len(stdout.strip()) > 0
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available Ollama models installed locally"""
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )
            
            if process.returncode != 0:
                return []
            
            lines = stdout.decode().strip().split('\n')
            models = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if parts:
                        model_name = parts[0].split(':')[0]
                        models.append(model_name)
            return models
        except Exception as e:
            print(f"[OllamaLocal] Error listing models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model if not already available"""
        try:
            print(f"[OllamaLocal] Pulling model: {model_name}")
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(
                process.communicate(),
                timeout=600
            )
            return process.returncode == 0
        except asyncio.TimeoutError:
            print(f"[OllamaLocal] Timeout pulling model: {model_name}")
            return False
        except Exception as e:
            print(f"[OllamaLocal] Error pulling model: {e}")
            return False
    
    async def generate(
        self,
        model_name: str,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """Generate response using ollama run command"""
        
        actual_model = model_name
        if model_name.startswith("ollama/"):
            actual_model = model_name[7:]
        elif model_name == "ollama":
            actual_model = self.default_model
            
        full_prompt = f"""System: {system_prompt}

"""
        if context:
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    full_prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    full_prompt += f"Assistant: {content}\n\n"
        
        full_prompt += f"User: {user_message}\n\nAssistant:"
        
        try:
            print(f"[OllamaLocal] Running model: {actual_model}")
            
            process = await asyncio.create_subprocess_exec(
                "ollama", "run", actual_model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=full_prompt.encode()),
                timeout=self.timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                if "not found" in error_msg.lower() or "pull" in error_msg.lower():
                    print(f"[OllamaLocal] Model not found, attempting to pull: {actual_model}")
                    pulled = await self.pull_model(actual_model)
                    if pulled:
                        return await self.generate(model_name, system_prompt, user_message, context)
                raise Exception(f"Ollama error: {error_msg}")
            
            response = stdout.decode().strip()
            if not response:
                raise Exception("Empty response from Ollama")
            
            return response
            
        except asyncio.TimeoutError:
            raise Exception(f"Ollama timeout ({self.timeout}s). Consider using a smaller model.")
        except FileNotFoundError:
            raise Exception("Ollama is not installed. Please install Ollama first: https://ollama.ai")
        except Exception as e:
            if "Ollama" not in str(e):
                raise Exception(f"Ollama error: {str(e)}")
            raise
    
    async def test_connection(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Test Ollama connection and model availability"""
        model = model_name or self.default_model
        if model.startswith("ollama/"):
            model = model[7:]
        
        if not await self.check_ollama_installed():
            return {
                "status": "error",
                "message": "Ollama is not installed. Please install from https://ollama.ai"
            }
        
        available_models = await self.list_models()
        
        if not available_models:
            return {
                "status": "warning",
                "message": f"No models installed. Run 'ollama pull {model}' to install."
            }
        
        if model not in available_models:
            return {
                "status": "warning",
                "message": f"Model '{model}' not found. Available: {', '.join(available_models[:5])}",
                "available_models": available_models
            }
        
        return {
            "status": "ok",
            "message": f"Ollama ready with model: {model}",
            "available_models": available_models
        }


ollama_client = OllamaLocalClient()
