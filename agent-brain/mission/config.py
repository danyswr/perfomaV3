import uuid
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.schemas.mission import (
    MissionConfigRequest,
    SavedConfig,
    StealthOptions,
    Capabilities,
    SessionSaveRequest,
    SavedSession
)


class ConfigManager:
    def __init__(self):
        self._configs: Dict[str, SavedConfig] = {}
        self._sessions: Dict[str, SavedSession] = {}
        self._lock = Lock()
        self._data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self._data_dir, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        configs_file = os.path.join(self._data_dir, "configs.json")
        sessions_file = os.path.join(self._data_dir, "sessions.json")
        
        if os.path.exists(configs_file):
            try:
                with open(configs_file, "r") as f:
                    data = json.load(f)
                    for config_data in data:
                        config_data["created_at"] = datetime.fromisoformat(config_data["created_at"])
                        config_data["updated_at"] = datetime.fromisoformat(config_data["updated_at"])
                        config_data["stealth_options"] = StealthOptions(**config_data.get("stealth_options", {}))
                        config_data["capabilities"] = Capabilities(**config_data.get("capabilities", {}))
                        self._configs[config_data["id"]] = SavedConfig(**config_data)
            except Exception as e:
                print(f"Error loading configs: {e}")

        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r") as f:
                    data = json.load(f)
                    for session_data in data:
                        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
                        session_data["updated_at"] = datetime.fromisoformat(session_data["updated_at"])
                        self._sessions[session_data["id"]] = SavedSession(**session_data)
            except Exception as e:
                print(f"Error loading sessions: {e}")

    def _save_to_disk(self):
        configs_file = os.path.join(self._data_dir, "configs.json")
        sessions_file = os.path.join(self._data_dir, "sessions.json")
        
        try:
            configs_data = []
            for config in self._configs.values():
                config_dict = config.model_dump()
                config_dict["created_at"] = config_dict["created_at"].isoformat()
                config_dict["updated_at"] = config_dict["updated_at"].isoformat()
                config_dict["stealth_options"] = config_dict["stealth_options"]
                config_dict["capabilities"] = config_dict["capabilities"]
                configs_data.append(config_dict)
            
            with open(configs_file, "w") as f:
                json.dump(configs_data, f, indent=2)
        except Exception as e:
            print(f"Error saving configs: {e}")

        try:
            sessions_data = []
            for session in self._sessions.values():
                session_dict = session.model_dump()
                session_dict["created_at"] = session_dict["created_at"].isoformat()
                session_dict["updated_at"] = session_dict["updated_at"].isoformat()
                sessions_data.append(session_dict)
            
            with open(sessions_file, "w") as f:
                json.dump(sessions_data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def save_config(self, request: MissionConfigRequest) -> SavedConfig:
        with self._lock:
            config_id = str(uuid.uuid4())
            now = datetime.now()
            
            config = SavedConfig(
                id=config_id,
                name=request.name,
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
                created_at=now,
                updated_at=now
            )
            
            self._configs[config_id] = config
            self._save_to_disk()
            return config

    def get_config(self, config_id: str) -> Optional[SavedConfig]:
        return self._configs.get(config_id)

    def get_all_configs(self) -> List[SavedConfig]:
        return list(self._configs.values())

    def delete_config(self, config_id: str) -> bool:
        with self._lock:
            if config_id in self._configs:
                del self._configs[config_id]
                self._save_to_disk()
                return True
            return False

    def save_session(self, request: SessionSaveRequest) -> SavedSession:
        with self._lock:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            session = SavedSession(
                id=session_id,
                name=request.name,
                config=request.config,
                agents=request.agents,
                findings=request.findings,
                created_at=now,
                updated_at=now
            )
            
            self._sessions[session_id] = session
            self._save_to_disk()
            return session

    def get_session(self, session_id: str) -> Optional[SavedSession]:
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[SavedSession]:
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self._save_to_disk()
                return True
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if session:
            return {
                "status": "loaded",
                "session": session.model_dump(),
                "config": session.config,
                "agents": session.agents,
                "findings": session.findings
            }
        return None


config_manager = ConfigManager()
