import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .cognitive import CognitiveEngine
from .decision import DecisionMaker
from memory.context import ContextManager
from reasoning.analyzer import ReasoningAnalyzer


class AgentBrain:
    """
    Central Intelligence for Agent System
    Handles reasoning, decision making, and cognitive processing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cognitive_engine = CognitiveEngine()
        self.decision_maker = DecisionMaker()
        self.context_manager = ContextManager()
        self.reasoning_analyzer = ReasoningAnalyzer()
        self.active = False
        self.thinking_history: List[Dict] = []
        
    async def initialize(self):
        """Initialize the brain and load models"""
        await self.cognitive_engine.load_models()
        self.active = True
        return {"status": "initialized", "timestamp": datetime.now().isoformat()}
    
    async def think(self, input_data: Dict) -> Dict:
        """
        Main thinking process - analyze input and generate intelligent response
        
        Args:
            input_data: Contains task, context, and constraints
            
        Returns:
            Thought process with recommendations and actions
        """
        if not self.active:
            await self.initialize()
            
        task = input_data.get("task", "")
        context = input_data.get("context", {})
        constraints = input_data.get("constraints", [])
        history = input_data.get("history", [])
        
        self.context_manager.update(context)
        
        analysis = await self.reasoning_analyzer.analyze(
            task=task,
            context=self.context_manager.get_full_context(),
            history=history
        )
        
        decision = await self.decision_maker.decide(
            analysis=analysis,
            constraints=constraints,
            available_actions=self._get_available_actions()
        )
        
        thought = {
            "id": f"thought-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "input_task": task,
            "analysis": analysis,
            "decision": decision,
            "confidence": decision.get("confidence", 0.0),
            "recommended_actions": decision.get("actions", []),
            "reasoning": decision.get("reasoning", "")
        }
        
        self.thinking_history.append(thought)
        
        return thought
    
    async def evaluate_action(self, action: Dict, context: Dict) -> Dict:
        """Evaluate if an action should be taken"""
        return await self.cognitive_engine.evaluate_action(action, context)
    
    async def classify_threat(self, finding: Dict) -> Dict:
        """Classify a security finding using fine-tuned models"""
        return await self.cognitive_engine.classify_threat(finding)
    
    async def generate_strategy(self, target: Dict, mode: str = "stealth") -> Dict:
        """Generate attack/defense strategy"""
        return await self.decision_maker.generate_strategy(target, mode)
    
    async def prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Prioritize tasks based on importance and context"""
        return await self.cognitive_engine.prioritize(tasks, self.context_manager.get_full_context())
    
    async def learn_from_outcome(self, action: Dict, outcome: Dict):
        """Learn from action outcomes to improve future decisions"""
        learning_data = {
            "action": action,
            "outcome": outcome,
            "context": self.context_manager.get_full_context(),
            "timestamp": datetime.now().isoformat()
        }
        await self.cognitive_engine.update_learning(learning_data)
    
    def _get_available_actions(self) -> List[str]:
        """Get list of available actions"""
        return [
            "scan_port",
            "enumerate_subdomain", 
            "analyze_vulnerability",
            "exploit_vulnerability",
            "gather_information",
            "lateral_movement",
            "privilege_escalation",
            "data_exfiltration",
            "report_finding",
            "wait_and_observe"
        ]
    
    async def get_status(self) -> Dict:
        """Get brain status"""
        return {
            "active": self.active,
            "models_loaded": await self.cognitive_engine.get_loaded_models(),
            "thinking_history_count": len(self.thinking_history),
            "context_size": self.context_manager.get_context_size()
        }
    
    async def reset(self):
        """Reset brain state"""
        self.thinking_history = []
        self.context_manager.reset()
        return {"status": "reset", "timestamp": datetime.now().isoformat()}
