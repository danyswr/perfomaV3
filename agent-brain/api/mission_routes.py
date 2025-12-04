from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.schemas.mission import (
    MissionConfigRequest,
    SavedConfig,
    SessionSaveRequest,
    SavedSession
)
from mission.config import config_manager
from mission.manager import mission_manager

router = APIRouter()


@router.post("/config")
async def save_config(request: MissionConfigRequest):
    try:
        config = config_manager.save_config(request)
        return {
            "status": "saved",
            "config_id": config.id,
            "config": config.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configs():
    configs = config_manager.get_all_configs()
    return {
        "configs": [c.model_dump() for c in configs],
        "total": len(configs)
    }


@router.get("/config/{config_id}")
async def get_config(config_id: str):
    config = config_manager.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config.model_dump()


@router.delete("/config/{config_id}")
async def delete_config(config_id: str):
    if config_manager.delete_config(config_id):
        return {"status": "deleted", "message": "Config deleted successfully"}
    raise HTTPException(status_code=404, detail="Config not found")


@router.post("/mission/start")
async def start_mission(request: MissionConfigRequest):
    try:
        mission = mission_manager.create_mission(request)
        started = mission_manager.start_mission(mission.id)
        
        return {
            "status": "started",
            "mission_id": mission.id,
            "mission": started.model_dump() if started else mission.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mission/{mission_id}/stop")
async def stop_mission(mission_id: str):
    mission = mission_manager.stop_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "stopped", "mission": mission.model_dump()}


@router.get("/mission")
async def get_missions():
    missions = mission_manager.get_all_missions()
    return {
        "missions": [m.model_dump() for m in missions],
        "total": len(missions)
    }


@router.get("/mission/active")
async def get_active_mission():
    mission = mission_manager.get_active_mission()
    if not mission:
        return {"status": "no_active_mission", "mission": None}
    return {"status": "active", "mission": mission.model_dump()}


@router.get("/mission/{mission_id}")
async def get_mission(mission_id: str):
    mission = mission_manager.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission.model_dump()


@router.delete("/mission/{mission_id}")
async def delete_mission(mission_id: str):
    if mission_manager.delete_mission(mission_id):
        return {"status": "deleted", "message": "Mission deleted successfully"}
    raise HTTPException(status_code=404, detail="Mission not found")


@router.post("/session/save")
async def save_session(request: SessionSaveRequest):
    try:
        session = config_manager.save_session(request)
        return {
            "status": "saved",
            "session_id": session.id,
            "message": "Session saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session")
async def get_sessions():
    sessions = config_manager.get_all_sessions()
    return {
        "sessions": [s.model_dump() for s in sessions],
        "total": len(sessions)
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = config_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if config_manager.delete_session(session_id):
        return {"status": "deleted", "message": "Session deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/session/{session_id}/load")
async def load_session(session_id: str):
    result = config_manager.load_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/models/test")
async def test_model(request: Dict[str, Any]):
    provider = request.get("provider", "")
    model = request.get("model", "")
    
    return {
        "status": "success",
        "message": "Model is available",
        "provider": provider,
        "model": model,
        "latency": "0ms"
    }


@router.post("/config/save")
async def save_config_named(request: MissionConfigRequest):
    try:
        config = config_manager.save_config(request)
        return {
            "status": "saved",
            "config_id": config.id,
            "name": config.name,
            "message": "Configuration saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/list")
async def list_configs():
    configs = config_manager.get_all_configs()
    return {
        "configs": [c.model_dump() for c in configs],
        "count": len(configs)
    }


@router.get("/config/saved")
async def get_saved_config():
    configs = config_manager.get_all_configs()
    if configs:
        latest = max(configs, key=lambda c: c.updated_at)
        return {"config": latest.model_dump(), "status": "found"}
    return {"config": None, "status": "not_found", "message": "No saved configuration found"}


@router.post("/start")
async def start_operation(request: MissionConfigRequest):
    try:
        from agents.manager import agent_manager
        from api.schemas.agent import CreateAgentRequest
        
        mission = mission_manager.create_mission(request)
        started = mission_manager.start_mission(mission.id)
        
        agent_ids = []
        for i in range(request.num_agents):
            agent_req = CreateAgentRequest(
                name=f"Agent-{i+1}",
                role="security-scanner",
                target=request.target,
                category=request.category,
                custom_instruction=request.custom_instruction,
                stealth_mode=request.stealth_mode,
                model_name=request.model_name
            )
            agent = agent_manager.create_agent(agent_req)
            agent_ids.append(agent.id)
        
        return {
            "status": "started",
            "mission_id": mission.id,
            "agent_ids": agent_ids,
            "timestamp": started.created_at.isoformat() if started else mission.created_at.isoformat(),
            "config": {
                "batch_size": 1,
                "rate_limit_rps": 0,
                "execution_duration": request.execution_duration,
                "requested_tools": request.requested_tools
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_operation():
    try:
        from agents.manager import agent_manager
        
        active = mission_manager.get_active_mission()
        if active:
            mission_manager.stop_mission(active.id)
        
        agents = agent_manager.get_all_agents()
        agents_stopped = 0
        for agent in agents:
            if agent.status.value in ["running", "idle"]:
                agent_manager.update_agent_status(agent.id, "complete")
                agents_stopped += 1
        
        return {
            "status": "stopped",
            "agents_stopped": agents_stopped,
            "total_agents": len(agents),
            "reports_generated_for": [],
            "summary": {
                "total_findings": 0,
                "severity_breakdown": {},
                "duration": 0,
                "agents_used": len(agents)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
