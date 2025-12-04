import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.schemas.agent import (
    Agent,
    AgentStatus,
    AgentConfig,
    AgentResources,
    AgentMessage,
    CreateAgentRequest
)


class AgentManager:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._messages: Dict[str, List[AgentMessage]] = {}
        self._lock = Lock()

    def create_agent(self, request: CreateAgentRequest) -> Agent:
        with self._lock:
            agent_id = str(uuid.uuid4())
            now = datetime.now()
            
            config = request.config or AgentConfig()
            if request.stealth_mode:
                config.stealth_mode = True
            
            agent = Agent(
                id=agent_id,
                name=request.name or f"Agent-{agent_id[:8]}",
                role=request.role,
                status=AgentStatus.IDLE,
                target=request.target,
                model=request.model_name,
                created_at=now,
                updated_at=now,
                task_count=0,
                findings=0,
                current_task="",
                config=config,
                resources=AgentResources(),
                progress=0
            )
            
            self._agents[agent_id] = agent
            self._messages[agent_id] = []
            
            if request.target:
                agent.status = AgentStatus.RUNNING
            
            return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:
        return list(self._agents.values())

    def delete_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                if agent_id in self._messages:
                    del self._messages[agent_id]
                return True
            return False

    def pause_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                if agent.status == AgentStatus.RUNNING:
                    agent.status = AgentStatus.PAUSED
                    agent.updated_at = datetime.now()
                    return True
            return False

    def resume_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                if agent.status == AgentStatus.PAUSED:
                    agent.status = AgentStatus.RUNNING
                    agent.updated_at = datetime.now()
                    return True
            return False

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.status = status
                agent.updated_at = datetime.now()
                return True
            return False

    def update_agent_resources(self, agent_id: str, resources: AgentResources) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.resources = resources
                agent.updated_at = datetime.now()
                return True
            return False

    def update_agent_progress(self, agent_id: str, progress: int, current_task: str = "") -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.progress = progress
                if current_task:
                    agent.current_task = current_task
                agent.updated_at = datetime.now()
                return True
            return False

    def increment_task_count(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.task_count += 1
                agent.updated_at = datetime.now()
                return True
            return False

    def increment_findings(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.findings += 1
                agent.updated_at = datetime.now()
                return True
            return False

    def add_message(self, agent_id: str, role: str, content: str, tool_used: Optional[str] = None) -> Optional[AgentMessage]:
        with self._lock:
            if agent_id in self._messages:
                msg = AgentMessage(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    role=role,
                    content=content,
                    timestamp=datetime.now(),
                    tool_used=tool_used
                )
                self._messages[agent_id].append(msg)
                return msg
            return None

    def get_messages(self, agent_id: str) -> List[AgentMessage]:
        return self._messages.get(agent_id, [])

    def clear_messages(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._messages:
                self._messages[agent_id] = []
                return True
            return False


agent_manager = AgentManager()
