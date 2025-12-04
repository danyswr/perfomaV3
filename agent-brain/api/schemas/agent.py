from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"


class StealthOptions(BaseModel):
    use_proxy: bool = False
    rotate_user_agent: bool = False
    delay_between_requests: int = 0
    max_concurrent_requests: int = 1
    avoid_detection: bool = False
    randomize_timing: bool = False


class Capabilities(BaseModel):
    web_scanning: bool = True
    port_scanning: bool = False
    vulnerability_detection: bool = True
    exploit_testing: bool = False
    report_generation: bool = True
    auto_escalation: bool = False


class AgentConfig(BaseModel):
    stealth_mode: bool = False
    aggressive_level: int = 1
    requested_tools: List[str] = []
    allowed_tools_only: bool = False
    stealth_options: StealthOptions = Field(default_factory=StealthOptions)
    capabilities: Capabilities = Field(default_factory=Capabilities)
    os_type: str = "linux"


class AgentResources(BaseModel):
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: float = 0.0


class Agent(BaseModel):
    id: str
    name: str
    role: str
    status: AgentStatus = AgentStatus.IDLE
    target: str = ""
    model: str = "openai/gpt-4-turbo"
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    findings: int = 0
    current_task: str = ""
    config: AgentConfig = Field(default_factory=AgentConfig)
    resources: AgentResources = Field(default_factory=AgentResources)
    progress: int = 0

    class Config:
        from_attributes = True


class AgentMessage(BaseModel):
    id: str
    agent_id: str
    role: str
    content: str
    timestamp: datetime
    tool_used: Optional[str] = None


class CreateAgentRequest(BaseModel):
    name: str = "Agent"
    role: str = "security-scanner"
    target: str = ""
    category: str = ""
    custom_instruction: str = ""
    stealth_mode: bool = False
    aggressive_mode: bool = False
    model_name: str = "openai/gpt-4-turbo"
    config: Optional[AgentConfig] = None
