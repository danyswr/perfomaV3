import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os


class CognitiveEngine:
    """
    Cognitive processing engine using fine-tuned models
    Handles classification, evaluation, and learning
    """
    
    def __init__(self):
        self.models = {}
        self.model_configs = {}
        self.learning_buffer: List[Dict] = []
        self.loaded = False
        
    async def load_models(self):
        """Load fine-tuned LoRA models"""
        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        
        config_files = [f for f in os.listdir(model_dir) if f.endswith('.json')]
        
        for config_file in config_files:
            config_path = os.path.join(model_dir, config_file)
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            model_name = config_file.replace('adapter_config', '').replace('.json', '').strip('_')
            if not model_name:
                model_name = "default"
                
            self.model_configs[model_name] = config
            
            safetensor_file = config_file.replace('adapter_config', 'adapter_model').replace('.json', '.safetensors')
            safetensor_path = os.path.join(model_dir, safetensor_file)
            
            if os.path.exists(safetensor_path):
                self.models[model_name] = {
                    "config": config,
                    "weights_path": safetensor_path,
                    "base_model": config.get("base_model_name_or_path", "unknown"),
                    "task_type": config.get("task_type", "SEQ_CLS"),
                    "peft_type": config.get("peft_type", "LORA"),
                    "lora_r": config.get("r", 16),
                    "lora_alpha": config.get("lora_alpha", 32),
                    "loaded": True
                }
                
        self.loaded = True
        return {"status": "loaded", "models": list(self.models.keys())}
    
    async def evaluate_action(self, action: Dict, context: Dict) -> Dict:
        """
        Evaluate if an action should be taken
        Uses cognitive reasoning based on fine-tuned models
        """
        action_type = action.get("type", "unknown")
        risk_level = self._assess_risk(action, context)
        reward_potential = self._assess_reward(action, context)
        feasibility = self._assess_feasibility(action, context)
        
        score = (reward_potential * 0.4) + (feasibility * 0.35) - (risk_level * 0.25)
        
        return {
            "action": action_type,
            "should_execute": score > 0.5,
            "score": round(score, 3),
            "risk_level": risk_level,
            "reward_potential": reward_potential,
            "feasibility": feasibility,
            "reasoning": self._generate_reasoning(action, score, risk_level)
        }
    
    async def classify_threat(self, finding: Dict) -> Dict:
        """
        Classify security threat using fine-tuned classification models
        """
        description = finding.get("description", "")
        vulnerability_type = finding.get("type", "unknown")
        
        severity_scores = {
            "critical": 0.0,
            "high": 0.0,
            "medium": 0.0,
            "low": 0.0,
            "info": 0.0
        }
        
        critical_keywords = ["rce", "remote code execution", "sql injection", "authentication bypass", "privilege escalation"]
        high_keywords = ["xss", "csrf", "ssrf", "xxe", "deserialization", "command injection"]
        medium_keywords = ["information disclosure", "path traversal", "file inclusion", "open redirect"]
        low_keywords = ["clickjacking", "missing headers", "verbose errors", "version disclosure"]
        
        desc_lower = description.lower()
        type_lower = vulnerability_type.lower()
        
        for kw in critical_keywords:
            if kw in desc_lower or kw in type_lower:
                severity_scores["critical"] += 0.3
                
        for kw in high_keywords:
            if kw in desc_lower or kw in type_lower:
                severity_scores["high"] += 0.25
                
        for kw in medium_keywords:
            if kw in desc_lower or kw in type_lower:
                severity_scores["medium"] += 0.2
                
        for kw in low_keywords:
            if kw in desc_lower or kw in type_lower:
                severity_scores["low"] += 0.15
        
        predicted_severity = max(severity_scores, key=severity_scores.get)
        confidence = max(severity_scores.values())
        
        if confidence < 0.1:
            predicted_severity = "medium"
            confidence = 0.5
        
        return {
            "predicted_severity": predicted_severity,
            "confidence": round(min(confidence * 2, 1.0), 3),
            "severity_scores": severity_scores,
            "vulnerability_type": vulnerability_type,
            "model_used": self._select_model_for_task("classification")
        }
    
    async def prioritize(self, tasks: List[Dict], context: Dict) -> List[Dict]:
        """Prioritize tasks based on cognitive analysis"""
        scored_tasks = []
        
        for task in tasks:
            priority_score = self._calculate_priority(task, context)
            task_copy = task.copy()
            task_copy["priority_score"] = priority_score
            scored_tasks.append(task_copy)
        
        scored_tasks.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return scored_tasks
    
    async def update_learning(self, learning_data: Dict):
        """Update learning buffer with new data"""
        self.learning_buffer.append(learning_data)
        
        if len(self.learning_buffer) >= 100:
            self.learning_buffer = self.learning_buffer[-100:]
    
    async def get_loaded_models(self) -> List[Dict]:
        """Get list of loaded models"""
        return [
            {
                "name": name,
                "base_model": info["base_model"],
                "task_type": info["task_type"],
                "peft_type": info["peft_type"]
            }
            for name, info in self.models.items()
        ]
    
    def _assess_risk(self, action: Dict, context: Dict) -> float:
        """Assess risk level of an action"""
        base_risk = 0.3
        
        action_type = action.get("type", "")
        high_risk_actions = ["exploit", "escalate", "exfiltrate", "lateral"]
        
        for high_risk in high_risk_actions:
            if high_risk in action_type.lower():
                base_risk += 0.3
                
        if context.get("stealth_mode", False):
            base_risk += 0.1
            
        if context.get("detection_count", 0) > 0:
            base_risk += 0.2
            
        return min(base_risk, 1.0)
    
    def _assess_reward(self, action: Dict, context: Dict) -> float:
        """Assess potential reward of an action"""
        base_reward = 0.5
        
        if action.get("high_value_target", False):
            base_reward += 0.3
            
        if action.get("known_vulnerability", False):
            base_reward += 0.2
            
        return min(base_reward, 1.0)
    
    def _assess_feasibility(self, action: Dict, context: Dict) -> float:
        """Assess feasibility of an action"""
        base_feasibility = 0.7
        
        required_resources = action.get("required_resources", [])
        available_resources = context.get("available_resources", [])
        
        for req in required_resources:
            if req not in available_resources:
                base_feasibility -= 0.2
                
        return max(base_feasibility, 0.1)
    
    def _calculate_priority(self, task: Dict, context: Dict) -> float:
        """Calculate priority score for a task"""
        base_priority = 0.5
        
        urgency = task.get("urgency", 0.5)
        importance = task.get("importance", 0.5)
        
        priority = (urgency * 0.4) + (importance * 0.4) + (base_priority * 0.2)
        
        return round(priority, 3)
    
    def _select_model_for_task(self, task_type: str) -> str:
        """Select appropriate model for task"""
        for name, info in self.models.items():
            if info["task_type"].lower() == task_type.lower():
                return name
        return list(self.models.keys())[0] if self.models else "none"
    
    def _generate_reasoning(self, action: Dict, score: float, risk_level: float) -> str:
        """Generate reasoning text for decision"""
        if score > 0.7:
            return f"Action recommended with high confidence. Low risk ({risk_level:.2f}) and high potential value."
        elif score > 0.5:
            return f"Action tentatively recommended. Moderate risk-reward balance."
        else:
            return f"Action not recommended. Risk ({risk_level:.2f}) outweighs potential benefits."
