import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, and_, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from .models import (
    Mission, MissionRun, Finding, AgentActivity, 
    ChatMessage, SavedProgress, MissionSummary,
    MissionStatus, AgentStatus, FindingSeverity
)

class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_mission(self, config: Dict[str, Any]) -> Mission:
        mission = Mission(
            mission_id=f"mission-{uuid.uuid4().hex[:8]}",
            target=config.get("target", ""),
            category=config.get("category", "domain"),
            custom_instruction=config.get("custom_instruction"),
            stealth_mode=config.get("stealth_mode", False),
            aggressive_level=config.get("aggressive_level", 1),
            model_name=config.get("model_name", "anthropic/claude-3.5-sonnet"),
            num_agents=config.get("num_agents", 3),
            os_type=config.get("os_type", "linux"),
            batch_size=config.get("batch_size", 20),
            rate_limit_rps=config.get("rate_limit_rps", 1.0),
            execution_duration=config.get("execution_duration"),
            requested_tools=config.get("requested_tools", []),
            stealth_options=config.get("stealth_options", {}),
            capabilities=config.get("capabilities", {}),
            status=MissionStatus.PENDING
        )
        self.session.add(mission)
        await self.session.flush()
        return mission
    
    async def get_mission(self, mission_id: str) -> Optional[Mission]:
        result = await self.session.execute(
            select(Mission).where(Mission.mission_id == mission_id)
        )
        return result.scalar_one_or_none()
    
    async def get_mission_by_pk(self, pk: int) -> Optional[Mission]:
        result = await self.session.execute(
            select(Mission).where(Mission.id == pk)
        )
        return result.scalar_one_or_none()
    
    async def update_mission_status(self, mission_id: str, status: MissionStatus):
        await self.session.execute(
            update(Mission)
            .where(Mission.mission_id == mission_id)
            .values(
                status=status,
                started_at=datetime.utcnow() if status == MissionStatus.RUNNING else None,
                ended_at=datetime.utcnow() if status in [MissionStatus.STOPPED, MissionStatus.COMPLETED] else None
            )
        )
    
    async def create_mission_run(self, mission_pk: int, agent_id: str, agent_number: int, target: str) -> MissionRun:
        run = MissionRun(
            run_id=f"run-{uuid.uuid4().hex[:8]}",
            mission_id=mission_pk,
            agent_id=agent_id,
            agent_number=agent_number,
            target=target,
            status=AgentStatus.IDLE
        )
        self.session.add(run)
        await self.session.flush()
        return run
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, **kwargs):
        values = {"status": status, **kwargs}
        await self.session.execute(
            update(MissionRun)
            .where(MissionRun.agent_id == agent_id)
            .values(**values)
        )
    
    async def create_finding(self, data: Dict[str, Any]) -> Finding:
        severity_str = data.get("severity", "info").lower()
        severity = FindingSeverity(severity_str) if severity_str in [s.value for s in FindingSeverity] else FindingSeverity.INFO
        
        finding = Finding(
            finding_id=f"finding-{uuid.uuid4().hex[:8]}",
            mission_id=data.get("mission_pk"),
            agent_id=data.get("agent_id"),
            title=data.get("title", "Unknown Finding"),
            description=data.get("description"),
            severity=severity,
            ip_address=data.get("ip_address"),
            port=data.get("port"),
            protocol=data.get("protocol"),
            service=data.get("service"),
            cve=data.get("cve"),
            cvss=data.get("cvss"),
            raw_output=data.get("raw_output"),
            details=data.get("details", {}),
            remediation=data.get("remediation"),
            tool_used=data.get("tool_used"),
            command_executed=data.get("command_executed")
        )
        self.session.add(finding)
        await self.session.flush()
        return finding
    
    async def get_findings(self, mission_id: Optional[str] = None, limit: int = 100) -> List[Finding]:
        query = select(Finding).order_by(desc(Finding.created_at)).limit(limit)
        if mission_id:
            query = query.join(Mission).where(Mission.mission_id == mission_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_findings_summary(self, mission_pk: Optional[int] = None) -> Dict[str, int]:
        findings = await self.get_findings()
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            if finding.severity:
                summary[finding.severity.value] = summary.get(finding.severity.value, 0) + 1
        return summary
    
    async def log_activity(self, data: Dict[str, Any]) -> AgentActivity:
        activity = AgentActivity(
            activity_id=f"activity-{uuid.uuid4().hex[:8]}",
            mission_id=data.get("mission_pk"),
            agent_id=data.get("agent_id", "system"),
            activity_type=data.get("activity_type", "unknown"),
            command=data.get("command"),
            output=data.get("output"),
            model_instruction=data.get("model_instruction"),
            model_response=data.get("model_response"),
            model_name=data.get("model_name"),
            tokens_used=data.get("tokens_used", 0),
            execution_time=data.get("execution_time", 0.0),
            status=data.get("status", "completed"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )
        self.session.add(activity)
        await self.session.flush()
        return activity
    
    async def get_activities(self, agent_id: Optional[str] = None, limit: int = 100) -> List[AgentActivity]:
        query = select(AgentActivity).order_by(desc(AgentActivity.created_at)).limit(limit)
        if agent_id:
            query = query.where(AgentActivity.agent_id == agent_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def save_chat_message(self, role: str, content: str, mission_id: Optional[str] = None, agent_id: Optional[str] = None) -> ChatMessage:
        message = ChatMessage(
            message_id=f"msg-{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            mission_id=mission_id,
            agent_id=agent_id
        )
        self.session.add(message)
        await self.session.flush()
        return message
    
    async def get_chat_history(self, mission_id: Optional[str] = None, limit: int = 100) -> List[ChatMessage]:
        query = select(ChatMessage).order_by(desc(ChatMessage.created_at)).limit(limit)
        if mission_id:
            query = query.where(ChatMessage.mission_id == mission_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def save_progress(self, mission_pk: int, name: str, description: str, state: Dict[str, Any]) -> SavedProgress:
        progress = SavedProgress(
            progress_id=f"progress-{uuid.uuid4().hex[:8]}",
            mission_id=mission_pk,
            name=name,
            description=description,
            mission_config=state.get("mission_config", {}),
            agent_states=state.get("agent_states", {}),
            queue_state=state.get("queue_state", {}),
            findings_snapshot=state.get("findings_snapshot", {})
        )
        self.session.add(progress)
        await self.session.flush()
        return progress
    
    async def get_saved_progress(self, progress_id: str) -> Optional[SavedProgress]:
        result = await self.session.execute(
            select(SavedProgress).where(SavedProgress.progress_id == progress_id)
        )
        return result.scalar_one_or_none()
    
    async def list_saved_progress(self, limit: int = 50) -> List[SavedProgress]:
        result = await self.session.execute(
            select(SavedProgress).order_by(desc(SavedProgress.created_at)).limit(limit)
        )
        return result.scalars().all()
    
    async def create_summary(self, mission_pk: int, data: Dict[str, Any]) -> MissionSummary:
        summary = MissionSummary(
            summary_id=f"summary-{uuid.uuid4().hex[:8]}",
            mission_id=mission_pk,
            total_findings=data.get("total_findings", 0),
            critical_count=data.get("critical_count", 0),
            high_count=data.get("high_count", 0),
            medium_count=data.get("medium_count", 0),
            low_count=data.get("low_count", 0),
            info_count=data.get("info_count", 0),
            open_ports=data.get("open_ports", []),
            services_found=data.get("services_found", []),
            vulnerabilities=data.get("vulnerabilities", []),
            targets_scanned=data.get("targets_scanned", []),
            agents_used=data.get("agents_used", 0),
            total_commands=data.get("total_commands", 0),
            total_tokens=data.get("total_tokens", 0),
            duration_seconds=data.get("duration_seconds", 0),
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
            summary_text=data.get("summary_text"),
            recommendations=data.get("recommendations", [])
        )
        self.session.add(summary)
        await self.session.flush()
        return summary
    
    async def get_latest_summary(self, mission_pk: int) -> Optional[MissionSummary]:
        result = await self.session.execute(
            select(MissionSummary)
            .where(MissionSummary.mission_id == mission_pk)
            .order_by(desc(MissionSummary.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_db_service():
    from .connection import get_async_session
    async with get_async_session() as session:
        if session:
            yield DatabaseService(session)
        else:
            yield None
