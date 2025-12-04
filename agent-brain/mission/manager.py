import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.schemas.mission import MissionConfig, MissionConfigRequest, StealthOptions, Capabilities


class MissionManager:
    def __init__(self):
        self._missions: Dict[str, MissionConfig] = {}
        self._active_mission: Optional[str] = None
        self._lock = Lock()

    def create_mission(self, request: MissionConfigRequest) -> MissionConfig:
        with self._lock:
            mission_id = str(uuid.uuid4())
            now = datetime.now()
            
            mission = MissionConfig(
                id=mission_id,
                name=request.name or f"Mission-{mission_id[:8]}",
                target=request.target,
                category=request.category,
                custom_instruction=request.custom_instruction,
                stealth_mode=request.stealth_mode,
                aggressive_level=request.aggressive_level,
                model_name=request.model_name,
                num_agents=request.num_agents,
                execution_duration=request.execution_duration,
                requested_tools=request.requested_tools,
                allowed_tools_only=request.allowed_tools_only,
                stealth_options=request.stealth_options,
                capabilities=request.capabilities,
                status="pending",
                created_at=now,
                updated_at=now
            )
            
            self._missions[mission_id] = mission
            return mission

    def start_mission(self, mission_id: str) -> Optional[MissionConfig]:
        with self._lock:
            if mission_id in self._missions:
                mission = self._missions[mission_id]
                mission.status = "running"
                mission.updated_at = datetime.now()
                self._active_mission = mission_id
                return mission
            return None

    def stop_mission(self, mission_id: str) -> Optional[MissionConfig]:
        with self._lock:
            if mission_id in self._missions:
                mission = self._missions[mission_id]
                mission.status = "stopped"
                mission.updated_at = datetime.now()
                if self._active_mission == mission_id:
                    self._active_mission = None
                return mission
            return None

    def complete_mission(self, mission_id: str) -> Optional[MissionConfig]:
        with self._lock:
            if mission_id in self._missions:
                mission = self._missions[mission_id]
                mission.status = "completed"
                mission.updated_at = datetime.now()
                if self._active_mission == mission_id:
                    self._active_mission = None
                return mission
            return None

    def get_mission(self, mission_id: str) -> Optional[MissionConfig]:
        return self._missions.get(mission_id)

    def get_all_missions(self) -> List[MissionConfig]:
        return list(self._missions.values())

    def get_active_mission(self) -> Optional[MissionConfig]:
        if self._active_mission:
            return self._missions.get(self._active_mission)
        return None

    def delete_mission(self, mission_id: str) -> bool:
        with self._lock:
            if mission_id in self._missions:
                if self._active_mission == mission_id:
                    self._active_mission = None
                del self._missions[mission_id]
                return True
            return False

    def update_mission_status(self, mission_id: str, status: str) -> Optional[MissionConfig]:
        with self._lock:
            if mission_id in self._missions:
                mission = self._missions[mission_id]
                mission.status = status
                mission.updated_at = datetime.now()
                return mission
            return None


mission_manager = MissionManager()
