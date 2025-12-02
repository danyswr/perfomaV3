from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os

brain_path = os.path.dirname(os.path.dirname(__file__))
if brain_path not in sys.path:
    sys.path.insert(0, brain_path)

from core.brain import AgentBrain
from memory.knowledge import KnowledgeBase
from reasoning.chain import ChainOfThought

router = APIRouter()

brain = AgentBrain()
knowledge_base = KnowledgeBase()
chain_of_thought = ChainOfThought()


class ThinkRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = {}
    constraints: Optional[List[str]] = []
    history: Optional[List[Dict]] = []


class ClassifyRequest(BaseModel):
    description: str
    type: Optional[str] = "unknown"
    additional_context: Optional[Dict[str, Any]] = {}


class EvaluateActionRequest(BaseModel):
    action: Dict[str, Any]
    context: Dict[str, Any]


class StrategyRequest(BaseModel):
    target: Dict[str, Any]
    mode: Optional[str] = "stealth"


class ReasonRequest(BaseModel):
    problem: str
    context: Optional[Dict[str, Any]] = {}


class LearnRequest(BaseModel):
    action: Dict[str, Any]
    outcome: Dict[str, Any]


class KnowledgeAddRequest(BaseModel):
    category: str
    data: Dict[str, Any]


class KnowledgeSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-brain"}


@router.get("/status")
async def get_status():
    """Get brain status"""
    return await brain.get_status()


@router.post("/initialize")
async def initialize_brain():
    """Initialize the brain and load models"""
    result = await brain.initialize()
    return result


@router.post("/think")
async def think(request: ThinkRequest):
    """
    Main thinking endpoint - analyze input and generate intelligent response
    """
    try:
        result = await brain.think({
            "task": request.task,
            "context": request.context,
            "constraints": request.constraints,
            "history": request.history
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_threat(request: ClassifyRequest):
    """
    Classify a security finding using fine-tuned models
    """
    try:
        result = await brain.classify_threat({
            "description": request.description,
            "type": request.type,
            **request.additional_context
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_action(request: EvaluateActionRequest):
    """
    Evaluate if an action should be taken
    """
    try:
        result = await brain.evaluate_action(request.action, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy")
async def generate_strategy(request: StrategyRequest):
    """
    Generate attack/assessment strategy for target
    """
    try:
        result = await brain.generate_strategy(request.target, request.mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reason")
async def chain_reason(request: ReasonRequest):
    """
    Apply chain-of-thought reasoning to a problem
    """
    try:
        result = await chain_of_thought.reason(request.problem, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prioritize")
async def prioritize_tasks(tasks: List[Dict[str, Any]]):
    """
    Prioritize tasks based on importance and context
    """
    try:
        result = await brain.prioritize_tasks(tasks)
        return {"prioritized_tasks": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn")
async def learn_from_outcome(request: LearnRequest):
    """
    Learn from action outcomes to improve future decisions
    """
    try:
        await brain.learn_from_outcome(request.action, request.outcome)
        return {"status": "learned", "action": request.action.get("type", "unknown")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/add")
async def add_to_knowledge(request: KnowledgeAddRequest):
    """
    Add knowledge to the knowledge base
    """
    try:
        if request.category == "vulnerability":
            knowledge_base.add_vulnerability(request.data)
        elif request.category == "pattern":
            knowledge_base.add_pattern(request.data)
        elif request.category == "strategy":
            knowledge_base.add_strategy(request.data)
        elif request.category == "behavior":
            knowledge_base.add_learned_behavior(request.data)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown category: {request.category}")
        
        return {"status": "added", "category": request.category}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/search")
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    Search the knowledge base
    """
    try:
        results = knowledge_base.search(request.query, request.category)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """
    Get knowledge base statistics
    """
    return knowledge_base.get_stats()


@router.get("/models")
async def get_loaded_models():
    """
    Get list of loaded fine-tuned models
    """
    return await brain.cognitive_engine.get_loaded_models()


@router.post("/reset")
async def reset_brain():
    """
    Reset brain state
    """
    return await brain.reset()
