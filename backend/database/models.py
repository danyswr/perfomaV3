from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class MissionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"

class AgentStatus(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"

class FindingSeverity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String(64), unique=True, nullable=False, index=True)
    target = Column(String(512), nullable=False)
    category = Column(String(32), default="domain")
    custom_instruction = Column(Text, nullable=True)
    stealth_mode = Column(Boolean, default=False)
    aggressive_level = Column(Integer, default=1)
    model_name = Column(String(128), default="anthropic/claude-3.5-sonnet")
    num_agents = Column(Integer, default=3)
    os_type = Column(String(16), default="linux")
    
    batch_size = Column(Integer, default=20)
    rate_limit_rps = Column(Float, default=1.0)
    execution_duration = Column(Integer, nullable=True)
    
    requested_tools = Column(JSON, default=list)
    stealth_options = Column(JSON, default=dict)
    capabilities = Column(JSON, default=dict)
    
    status = Column(SQLEnum(MissionStatus), default=MissionStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    runs = relationship("MissionRun", back_populates="mission", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="mission", cascade="all, delete-orphan")
    activities = relationship("AgentActivity", back_populates="mission", cascade="all, delete-orphan")
    summaries = relationship("MissionSummary", back_populates="mission", cascade="all, delete-orphan")
    saved_progress = relationship("SavedProgress", back_populates="mission", cascade="all, delete-orphan")

class MissionRun(Base):
    __tablename__ = "mission_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    
    agent_id = Column(String(64), nullable=False, index=True)
    agent_number = Column(Integer, default=1)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)
    
    target = Column(String(512), nullable=True)
    current_task = Column(Text, nullable=True)
    last_command = Column(Text, nullable=True)
    last_output = Column(Text, nullable=True)
    
    tasks_completed = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    execution_time = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    mission = relationship("Mission", back_populates="runs")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(64), unique=True, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    agent_id = Column(String(64), nullable=True, index=True)
    
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(FindingSeverity), default=FindingSeverity.INFO)
    
    ip_address = Column(String(64), nullable=True)
    port = Column(Integer, nullable=True)
    protocol = Column(String(16), nullable=True)
    service = Column(String(128), nullable=True)
    
    cve = Column(String(32), nullable=True)
    cvss = Column(Float, nullable=True)
    
    raw_output = Column(Text, nullable=True)
    details = Column(JSON, default=dict)
    remediation = Column(Text, nullable=True)
    
    tool_used = Column(String(64), nullable=True)
    command_executed = Column(Text, nullable=True)
    
    verified = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    mission = relationship("Mission", back_populates="findings")

class AgentActivity(Base):
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String(64), unique=True, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    agent_id = Column(String(64), nullable=False, index=True)
    
    activity_type = Column(String(32), nullable=False)
    command = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    
    model_instruction = Column(Text, nullable=True)
    model_response = Column(Text, nullable=True)
    model_name = Column(String(128), nullable=True)
    
    tokens_used = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    
    status = Column(String(32), default="pending")
    error_message = Column(Text, nullable=True)
    
    metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, server_default=func.now())
    
    mission = relationship("Mission", back_populates="activities")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(64), unique=True, nullable=False, index=True)
    
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    
    mission_id = Column(String(64), nullable=True, index=True)
    agent_id = Column(String(64), nullable=True, index=True)
    
    metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, server_default=func.now())

class SavedProgress(Base):
    __tablename__ = "saved_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    progress_id = Column(String(64), unique=True, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    
    mission_config = Column(JSON, default=dict)
    agent_states = Column(JSON, default=dict)
    queue_state = Column(JSON, default=dict)
    findings_snapshot = Column(JSON, default=dict)
    
    can_resume = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    mission = relationship("Mission", back_populates="saved_progress")

class MissionSummary(Base):
    __tablename__ = "mission_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_id = Column(String(64), unique=True, nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    
    open_ports = Column(JSON, default=list)
    services_found = Column(JSON, default=list)
    vulnerabilities = Column(JSON, default=list)
    
    targets_scanned = Column(JSON, default=list)
    agents_used = Column(Integer, default=0)
    total_commands = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    duration_seconds = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    summary_text = Column(Text, nullable=True)
    recommendations = Column(JSON, default=list)
    
    created_at = Column(DateTime, server_default=func.now())
    
    mission = relationship("Mission", back_populates="summaries")
