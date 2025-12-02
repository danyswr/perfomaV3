from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


class KnowledgeBase:
    """
    Long-term knowledge storage for agent
    Stores learned patterns, findings, and strategies
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "knowledge"
        )
        self.knowledge: Dict[str, List[Dict]] = {
            "vulnerabilities": [],
            "patterns": [],
            "strategies": [],
            "learned_behaviors": []
        }
        self._ensure_storage()
        self._load_knowledge()
    
    def _ensure_storage(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_knowledge(self):
        """Load knowledge from storage"""
        knowledge_file = os.path.join(self.storage_path, "knowledge.json")
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, 'r') as f:
                    self.knowledge = json.load(f)
            except:
                pass
    
    def _save_knowledge(self):
        """Save knowledge to storage"""
        knowledge_file = os.path.join(self.storage_path, "knowledge.json")
        with open(knowledge_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
    
    def add_vulnerability(self, vuln: Dict):
        """Add a vulnerability to knowledge base"""
        vuln["added_at"] = datetime.now().isoformat()
        self.knowledge["vulnerabilities"].append(vuln)
        self._save_knowledge()
    
    def add_pattern(self, pattern: Dict):
        """Add a recognized pattern"""
        pattern["added_at"] = datetime.now().isoformat()
        self.knowledge["patterns"].append(pattern)
        self._save_knowledge()
    
    def add_strategy(self, strategy: Dict):
        """Add a successful strategy"""
        strategy["added_at"] = datetime.now().isoformat()
        self.knowledge["strategies"].append(strategy)
        self._save_knowledge()
    
    def add_learned_behavior(self, behavior: Dict):
        """Add a learned behavior"""
        behavior["added_at"] = datetime.now().isoformat()
        self.knowledge["learned_behaviors"].append(behavior)
        self._save_knowledge()
    
    def search(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search knowledge base"""
        results = []
        query_lower = query.lower()
        
        categories = [category] if category else list(self.knowledge.keys())
        
        for cat in categories:
            if cat in self.knowledge:
                for item in self.knowledge[cat]:
                    item_str = json.dumps(item).lower()
                    if query_lower in item_str:
                        results.append({**item, "category": cat})
        
        return results
    
    def get_similar_vulnerabilities(self, vuln_type: str) -> List[Dict]:
        """Get similar vulnerabilities from knowledge base"""
        return [
            v for v in self.knowledge["vulnerabilities"]
            if vuln_type.lower() in json.dumps(v).lower()
        ]
    
    def get_effective_strategies(self, target_type: str) -> List[Dict]:
        """Get strategies that worked for similar targets"""
        return [
            s for s in self.knowledge["strategies"]
            if s.get("success", False) and target_type.lower() in json.dumps(s).lower()
        ]
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            category: len(items)
            for category, items in self.knowledge.items()
        }
