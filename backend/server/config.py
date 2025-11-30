from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration - Multiple providers
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    CUSTOM_MODEL_API_KEY: str = os.getenv("CUSTOM_MODEL_API_KEY", "")
    CUSTOM_MODEL_ENDPOINT: str = os.getenv("CUSTOM_MODEL_ENDPOINT", "")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Directory Configuration
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    FINDINGS_DIR: str = os.getenv("FINDINGS_DIR", "./findings")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cybersec_agents.db")
    
    # Resource Limits
    MAX_MEMORY_PERCENT: int = int(os.getenv("MAX_MEMORY_PERCENT", "80"))
    MAX_CPU_PERCENT: int = int(os.getenv("MAX_CPU_PERCENT", "90"))
    
    # Rate Limiting
    DEFAULT_DELAY_MIN: float = float(os.getenv("DEFAULT_DELAY_MIN", "1"))
    DEFAULT_DELAY_MAX: float = float(os.getenv("DEFAULT_DELAY_MAX", "3"))
    
    ENABLE_PROXY: bool = os.getenv("ENABLE_PROXY", "false").lower() == "true"
    PROXY_LIST: str = os.getenv("PROXY_LIST", "")  # Comma-separated proxy URLs
    ENABLE_TOR: bool = os.getenv("ENABLE_TOR", "false").lower() == "true"
    TOR_SOCKS_PORT: int = int(os.getenv("TOR_SOCKS_PORT", "9050"))
    
    # User Agent Strategy: random, weighted, sequential
    UA_ROTATION_STRATEGY: str = os.getenv("UA_ROTATION_STRATEGY", "weighted")
    
    # Timing Strategy: uniform, exponential, gaussian, human_like
    TIMING_STRATEGY: str = os.getenv("TIMING_STRATEGY", "human_like")
    
    # Proxy Strategy: random, round_robin, performance
    PROXY_STRATEGY: str = os.getenv("PROXY_STRATEGY", "random")
    
    # Traffic Obfuscation
    ENABLE_TRAFFIC_OBFUSCATION: bool = os.getenv("ENABLE_TRAFFIC_OBFUSCATION", "true").lower() == "true"
    
    # Fingerprint Rotation
    FINGERPRINT_ROTATION_INTERVAL: int = int(os.getenv("FINGERPRINT_ROTATION_INTERVAL", "100"))  # Per N requests
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Agent Configuration
    MAX_AGENTS: int = 10
    
    def get_proxy_list(self) -> List[str]:
        """Parse comma-separated proxy list"""
        if not self.PROXY_LIST:
            proxies = []
        else:
            proxies = [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]
        
        # Add TOR if enabled
        if self.ENABLE_TOR:
            proxies.append(f"socks5://127.0.0.1:{self.TOR_SOCKS_PORT}")
        
        return proxies
    
    class Config:
        env_file = ".env"

settings = Settings()
