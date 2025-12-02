from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class ContextManager:
    """
    Manages context and working memory for agent reasoning
    """
    
    def __init__(self, max_context_size: int = 1000):
        self.current_context: Dict[str, Any] = {}
        self.context_history: List[Dict] = []
        self.max_context_size = max_context_size
        self.working_memory: Dict[str, Any] = {}
        
    def update(self, new_context: Dict):
        """Update context with new information"""
        timestamp = datetime.now().isoformat()
        
        self.context_history.append({
            "context": self.current_context.copy(),
            "timestamp": timestamp
        })
        
        self._merge_context(new_context)
        
        self._prune_history()
    
    def _merge_context(self, new_context: Dict):
        """Merge new context into current context"""
        for key, value in new_context.items():
            if key in self.current_context and isinstance(value, list):
                existing = self.current_context[key]
                if isinstance(existing, list):
                    self.current_context[key] = existing + value
                else:
                    self.current_context[key] = value
            elif key in self.current_context and isinstance(value, dict):
                existing = self.current_context[key]
                if isinstance(existing, dict):
                    existing.update(value)
                else:
                    self.current_context[key] = value
            else:
                self.current_context[key] = value
    
    def _prune_history(self):
        """Prune old context history to maintain size limit"""
        if len(self.context_history) > self.max_context_size:
            self.context_history = self.context_history[-self.max_context_size:]
    
    def get_full_context(self) -> Dict:
        """Get full current context"""
        return {
            "current": self.current_context,
            "working_memory": self.working_memory,
            "history_size": len(self.context_history),
            "last_update": self.context_history[-1]["timestamp"] if self.context_history else None
        }
    
    def get_context_size(self) -> int:
        """Get current context size"""
        return len(json.dumps(self.current_context))
    
    def set_working_memory(self, key: str, value: Any):
        """Set a value in working memory"""
        self.working_memory[key] = {
            "value": value,
            "set_at": datetime.now().isoformat()
        }
    
    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get a value from working memory"""
        if key in self.working_memory:
            return self.working_memory[key]["value"]
        return None
    
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory = {}
    
    def reset(self):
        """Reset all context"""
        self.current_context = {}
        self.context_history = []
        self.working_memory = {}
    
    def summarize_context(self) -> Dict:
        """Get a summary of current context"""
        return {
            "keys": list(self.current_context.keys()),
            "size": self.get_context_size(),
            "history_length": len(self.context_history),
            "working_memory_keys": list(self.working_memory.keys())
        }
