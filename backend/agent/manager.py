import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from agent.worker import AgentWorker
from agent.queue import QueueManager
from agent.collaboration import InterAgentCommunication, AgentCapability
from monitor.log import Logger
from monitor.resource import ResourceMonitor
import json

class AgentManager:
    """Manages multiple autonomous agents"""
    
    def __init__(self):
        self.agents: Dict[str, AgentWorker] = {}
        self.queue_manager = QueueManager()
        self.logger = Logger()
        self.resource_monitor = ResourceMonitor()
        self.collaboration_bus = InterAgentCommunication()
        self.shared_knowledge: Dict[str, Any] = {
            "findings": [],
            "messages": [],
            "vulnerabilities": []
        }
        self.operation_active = False
        
    async def create_agents(
        self,
        num_agents: int,
        target: str,
        category: str,
        custom_instruction: Optional[str],
        stealth_mode: bool,
        aggressive_mode: bool,
        model_name: str,
        stealth_config: Optional[Dict] = None,
        os_type: str = "linux",
        stealth_options: Optional[Dict] = None,
        capabilities: Optional[Dict] = None,
        batch_size: int = 20,
        rate_limit_rps: float = 1.0,
        execution_duration: Optional[int] = None,
        requested_tools: Optional[List[str]] = None,
        allowed_tools_only: bool = False
    ) -> List[str]:
        """Create multiple agents for operation"""
        agent_ids = []
        
        if stealth_config is None and stealth_mode:
            from server.config import settings
            stealth_config = {
                "proxies": settings.get_proxy_list(),
                "ua_strategy": settings.UA_ROTATION_STRATEGY,
                "timing_strategy": settings.TIMING_STRATEGY,
                "proxy_strategy": settings.PROXY_STRATEGY,
                "enable_obfuscation": settings.ENABLE_TRAFFIC_OBFUSCATION,
                "min_delay": settings.DEFAULT_DELAY_MIN * 2,
                "max_delay": settings.DEFAULT_DELAY_MAX * 3,
            }
        
        for i in range(num_agents):
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            
            agent = AgentWorker(
                agent_id=agent_id,
                agent_number=i + 1,
                target=target,
                category=category,
                custom_instruction=custom_instruction,
                stealth_mode=stealth_mode,
                aggressive_mode=aggressive_mode,
                model_name=model_name,
                shared_knowledge=self.shared_knowledge,
                logger=self.logger,
                stealth_config=stealth_config,
                os_type=os_type,
                stealth_options=stealth_options,
                capabilities=capabilities,
                batch_size=batch_size,
                rate_limit_rps=rate_limit_rps,
                execution_duration=execution_duration,
                requested_tools=requested_tools or [],
                allowed_tools_only=allowed_tools_only
            )
            
            self.agents[agent_id] = agent
            agent_ids.append(agent_id)
            
            cap = AgentCapability(
                agent_id=agent_id,
                specializations=["general"],
                current_load=0.0,
                status="idle",
                target=target,
                tools_available=requested_tools or [],
                findings_count=0
            )
            await self.collaboration_bus.register_agent(agent_id, cap)
            
            await self.logger.log_event(
                f"Agent {agent_id} created",
                "system",
                {"agent_number": i + 1, "target": target, "batch_size": batch_size, "rate_limit": rate_limit_rps}
            )
        
        return agent_ids
    
    async def start_operation(self, agent_ids: List[str], config: Dict):
        """Start autonomous operation with all agents"""
        self.operation_active = True
        target = config.get("target", "general")
        
        await self.logger.log_event(
            "Operation started",
            "system",
            {"num_agents": len(agent_ids), "target": target}
        )
        
        # Start all agents concurrently
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                tasks.append(agent.start())
        
        # Run all agents
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Generate final report with target folder organization
        await self.generate_report(target=target)
        
        self.operation_active = False
        
        await self.logger.log_event(
            "Operation completed",
            "system",
            {"num_agents": len(agent_ids)}
        )
    
    async def get_all_agents(self) -> List[Dict]:
        """Get status of all agents"""
        agents_status = []
        
        for agent_id, agent in self.agents.items():
            status = await agent.get_status()
            # Add resource usage
            resources = await self.resource_monitor.get_agent_resource(agent_id)
            status["resources"] = resources
            agents_status.append(status)
        
        return agents_status
    
    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get specific agent status"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        status = await agent.get_status()
        resources = await self.resource_monitor.get_agent_resource(agent_id)
        status["resources"] = resources
        
        return status
    
    async def create_single_agent(
        self,
        target: str = "",
        category: str = "domain",
        custom_instruction: Optional[str] = None,
        stealth_mode: bool = False,
        aggressive_mode: bool = False,
        model_name: str = "openai/gpt-4-turbo",
        auto_start: bool = True
    ) -> Optional[str]:
        """Create a single agent manually and optionally start it"""
        if len(self.agents) >= 10:
            return None
        
        agent_number = len(self.agents) + 1
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        
        agent = AgentWorker(
            agent_id=agent_id,
            agent_number=agent_number,
            target=target,
            category=category,
            custom_instruction=custom_instruction,
            stealth_mode=stealth_mode,
            aggressive_mode=aggressive_mode,
            model_name=model_name,
            shared_knowledge=self.shared_knowledge,
            logger=self.logger,
            stealth_config=None
        )
        
        self.agents[agent_id] = agent
        
        await self.logger.log_event(
            f"Agent {agent_id} created manually",
            "system",
            {"agent_number": agent_number}
        )
        
        if auto_start:
            async def safe_start():
                try:
                    await agent.start()
                except Exception as e:
                    await self.logger.log_event(
                        f"Agent {agent_id} start error: {str(e)}",
                        "error",
                        {"agent_id": agent_id}
                    )
            asyncio.create_task(safe_start())
            await self.logger.log_event(
                f"Agent {agent_id} started automatically",
                "system",
                {"target": target or "awaiting target"}
            )
        
        return agent_id

    async def delete_agent(self, agent_id: str) -> bool:
        """Stop and delete an agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        await agent.stop()
        del self.agents[agent_id]
        
        await self.logger.log_event(
            f"Agent {agent_id} deleted",
            "system"
        )
        
        return True
    
    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        await agent.pause()
        
        return True
    
    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        await agent.resume()
        
        return True
    
    async def stop_all_agents(self) -> Dict:
        """Stop all agents immediately and generate final reports with summary"""
        self.operation_active = False
        stopped_count = 0
        start_time = None
        
        await self.logger.log_event(
            "Stopping all agents",
            "system",
            {"num_agents": len(self.agents)}
        )
        
        targets_set = set()
        
        for agent_id, agent in self.agents.items():
            try:
                targets_set.add(agent.target)
                if agent.start_time and (start_time is None or agent.start_time < start_time):
                    start_time = agent.start_time
                await agent.stop()
                stopped_count += 1
                await self.logger.log_event(
                    f"Agent {agent_id} stopped",
                    "system"
                )
            except Exception as e:
                await self.logger.log_event(
                    f"Error stopping agent {agent_id}: {str(e)}",
                    "error"
                )
        
        await asyncio.sleep(0.5)
        
        await self.logger.log_event(
            f"All agents stopped ({stopped_count}/{len(self.agents)})",
            "system"
        )
        
        for target in targets_set:
            try:
                await self.generate_report(target=target)
            except Exception as e:
                await self.logger.log_event(
                    f"Error generating report for {target}: {str(e)}",
                    "error"
                )
        
        findings = self.shared_knowledge.get("findings", [])
        severity_summary = await self.get_severity_summary()
        
        import time
        duration = int(time.time() - start_time) if start_time else 0
        
        summary = {
            "total_findings": len(findings),
            "severity_breakdown": severity_summary,
            "duration": duration,
            "agents_used": len(self.agents),
            "targets_scanned": list(targets_set)
        }
        
        await self.logger.log_event(
            "Mission completed",
            "system",
            summary
        )
        
        return {
            "status": "stopped",
            "agents_stopped": stopped_count,
            "total_agents": len(self.agents),
            "reports_generated_for": list(targets_set),
            "summary": summary
        }
    
    async def get_agent_instruction_history(self, agent_id: str) -> List[Dict]:
        """Get instruction history for a specific agent"""
        if agent_id not in self.agents:
            return []
        
        agent = self.agents[agent_id]
        return agent.get_instruction_history()
    
    async def get_all_instruction_history(self) -> List[Dict]:
        """Get combined instruction history from all agents"""
        all_history = []
        for agent_id, agent in self.agents.items():
            history = agent.get_instruction_history()
            for item in history:
                item["agent_id"] = agent_id
            all_history.extend(history)
        
        # Sort by timestamp
        all_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_history[:100]  # Return last 100 instructions
    
    async def get_findings(self) -> List[Dict]:
        """Get all findings from shared knowledge base"""
        return self.shared_knowledge.get("findings", [])
    
    async def get_severity_summary(self) -> Dict:
        """Get summary of findings by severity"""
        findings = self.shared_knowledge.get("findings", [])
        
        summary = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Info": 0
        }
        
        for finding in findings:
            severity = finding.get("severity", "Info")
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    async def generate_report(self, target: Optional[str] = None):
        """Generate final report of all findings - JSON/TXT/PDF only (no HTML)"""
        from monitor.log import ReportGenerator
        
        report_gen = ReportGenerator(self.shared_knowledge, target=target)
        
        txt_path = await report_gen.generate_txt_report()
        json_path = await report_gen.export_json()
        pdf_path = await report_gen.generate_pdf()
        
        await self.logger.log_event(
            "Reports generated",
            "system",
            {
                "txt": txt_path,
                "json": json_path,
                "pdf": pdf_path
            }
        )
        
        return {
            "txt": txt_path,
            "json": json_path,
            "pdf": pdf_path
        }
