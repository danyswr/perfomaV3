from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


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


class MissionConfigRequest(BaseModel):
    name: str = ""
    target: str
    category: str = "url"
    custom_instruction: str = ""
    stealth_mode: bool = False
    aggressive_level: int = 1
    model_name: str = "openai/gpt-4-turbo"
    num_agents: int = 1
    execution_duration: Optional[int] = None
    requested_tools: List[str] = []
    allowed_tools_only: bool = False
    stealth_options: StealthOptions = Field(default_factory=StealthOptions)
    capabilities: Capabilities = Field(default_factory=Capabilities)


class MissionConfig(BaseModel):
    id: str
    name: str
    target: str
    category: str
    custom_instruction: str
    stealth_mode: bool
    aggressive_level: int
    model_name: str
    num_agents: int
    execution_duration: Optional[int]
    requested_tools: List[str]
    allowed_tools_only: bool
    stealth_options: StealthOptions
    capabilities: Capabilities
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


class SavedConfig(BaseModel):
    id: str
    name: str
    target: str
    category: str
    custom_instruction: str
    stealth_mode: bool
    aggressive_level: int
    model_name: str
    num_agents: int
    execution_duration: Optional[int]
    requested_tools: List[str]
    allowed_tools_only: bool
    stealth_options: StealthOptions
    capabilities: Capabilities
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionSaveRequest(BaseModel):
    name: str
    config: Optional[Dict[str, Any]] = None
    agents: Optional[List[Dict[str, Any]]] = None
    findings: Optional[List[Dict[str, Any]]] = None


class SavedSession(BaseModel):
    id: str
    name: str
    config: Optional[Dict[str, Any]] = None
    agents: Optional[List[Dict[str, Any]]] = None
    findings: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
