from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.schemas.agent import CreateAgentRequest, AgentResources
from agents.manager import agent_manager

router = APIRouter()


@router.post("/agents")
async def create_agent(request: CreateAgentRequest):
    try:
        agent = agent_manager.create_agent(request)
        return {
            "status": "created",
            "agent_id": agent.id,
            "agent": agent.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents():
    agents = agent_manager.get_all_agents()
    return {
        "agents": [a.model_dump() for a in agents],
        "total": len(agents)
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    messages = agent_manager.get_messages(agent_id)
    return {
        "agent": agent.model_dump(),
        "messages": [m.model_dump() for m in messages]
    }


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if agent_manager.delete_agent(agent_id):
        return {"message": "Agent deleted successfully"}
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str):
    if agent_manager.pause_agent(agent_id):
        return {"message": "Agent paused successfully"}
    raise HTTPException(status_code=400, detail="Cannot pause agent")


@router.post("/agents/{agent_id}/resume")
async def resume_agent(agent_id: str):
    if agent_manager.resume_agent(agent_id):
        return {"message": "Agent resumed successfully"}
    raise HTTPException(status_code=400, detail="Cannot resume agent")


@router.post("/agents/{agent_id}/message")
async def add_agent_message(agent_id: str, request: Dict[str, Any]):
    role = request.get("role", "user")
    content = request.get("content", "")
    tool_used = request.get("tool_used")
    
    msg = agent_manager.add_message(agent_id, role, content, tool_used)
    if msg:
        return {"status": "added", "message": msg.model_dump()}
    raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/agents/{agent_id}/messages")
async def get_agent_messages(agent_id: str):
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    messages = agent_manager.get_messages(agent_id)
    return {
        "agent_id": agent_id,
        "messages": [m.model_dump() for m in messages],
        "total": len(messages)
    }


@router.post("/agents/{agent_id}/resources")
async def update_agent_resources(agent_id: str, resources: AgentResources):
    if agent_manager.update_agent_resources(agent_id, resources):
        return {"status": "updated", "message": "Resources updated successfully"}
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/agents/{agent_id}/progress")
async def update_agent_progress(agent_id: str, request: Dict[str, Any]):
    progress = request.get("progress", 0)
    current_task = request.get("current_task", "")
    
    if agent_manager.update_agent_progress(agent_id, progress, current_task):
        return {"status": "updated", "message": "Progress updated successfully"}
    raise HTTPException(status_code=404, detail="Agent not found")
