import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

class MessageType(Enum):
    """Types of inter-agent messages"""
    DISCOVERY = "discovery"
    FINDING = "finding"
    REQUEST_HELP = "request_help"
    OFFER_HELP = "offer_help"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    STATUS_UPDATE = "status_update"
    KNOWLEDGE_SHARE = "knowledge_share"
    ALERT = "alert"
    COORDINATION = "coordination"

class Priority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 7
    CRITICAL = 10

@dataclass
class AgentMessage:
    """Structured message between agents"""
    id: str
    from_agent: str
    to_agent: Optional[str]
    message_type: MessageType
    content: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    requires_ack: bool = False
    ack_received: bool = False
    metadata: Dict = field(default_factory=dict)

@dataclass
class AgentCapability:
    """Describes an agent's capabilities"""
    agent_id: str
    specializations: List[str]
    current_load: float
    status: str
    target: str
    tools_available: List[str]
    findings_count: int

class InterAgentCommunication:
    """
    Inter-Agent Communication System
    
    Enables agents to:
    - Send direct messages to specific agents
    - Broadcast messages to all agents
    - Share findings and knowledge
    - Request/offer help for specific tasks
    - Coordinate to avoid duplicate work
    """
    
    def __init__(self):
        self._message_queue: Dict[str, List[AgentMessage]] = {}
        self._agent_capabilities: Dict[str, AgentCapability] = {}
        self._subscriptions: Dict[str, List[MessageType]] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._message_counter = 0
        self._lock = asyncio.Lock()
        
        self._shared_discoveries: Dict[str, Any] = {}
        self._completed_tasks: set = set()
        self._in_progress_tasks: Dict[str, str] = {}
        
        self._max_messages_per_agent = 20
        self._max_discoveries = 100
        self._max_completed_tasks = 50
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        self._message_counter += 1
        return f"msg-{self._message_counter:06d}-{datetime.now().strftime('%H%M%S')}"
    
    async def register_agent(self, agent_id: str, capabilities: AgentCapability):
        """Register an agent with the communication system"""
        async with self._lock:
            self._agent_capabilities[agent_id] = capabilities
            if agent_id not in self._message_queue:
                self._message_queue[agent_id] = []
            if agent_id not in self._subscriptions:
                self._subscriptions[agent_id] = list(MessageType)
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        async with self._lock:
            if agent_id in self._agent_capabilities:
                del self._agent_capabilities[agent_id]
            if agent_id in self._message_queue:
                del self._message_queue[agent_id]
    
    async def update_capabilities(self, agent_id: str, **updates):
        """Update agent capabilities"""
        async with self._lock:
            if agent_id in self._agent_capabilities:
                cap = self._agent_capabilities[agent_id]
                for key, value in updates.items():
                    if hasattr(cap, key):
                        setattr(cap, key, value)
    
    def _trim_queue(self, agent_id: str):
        """Trim message queue for an agent to prevent memory growth"""
        if agent_id in self._message_queue:
            queue = self._message_queue[agent_id]
            if len(queue) > self._max_messages_per_agent:
                excess = len(queue) - self._max_messages_per_agent
                del queue[:excess]
    
    def _trim_discoveries(self):
        """Trim discoveries to prevent memory growth"""
        if len(self._shared_discoveries) > self._max_discoveries:
            keys = list(self._shared_discoveries.keys())
            for key in keys[:len(keys) - self._max_discoveries]:
                del self._shared_discoveries[key]
    
    def _trim_completed_tasks(self):
        """Trim completed tasks set"""
        if len(self._completed_tasks) > self._max_completed_tasks:
            excess = len(self._completed_tasks) - self._max_completed_tasks
            tasks_list = list(self._completed_tasks)
            for task in tasks_list[:excess]:
                self._completed_tasks.discard(task)
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to a specific agent or broadcast"""
        async with self._lock:
            message.id = self._generate_message_id()
            
            if message.to_agent:
                if message.to_agent in self._message_queue:
                    self._message_queue[message.to_agent].append(message)
                    self._trim_queue(message.to_agent)
                    
                    if message.to_agent in self._message_handlers:
                        try:
                            await self._message_handlers[message.to_agent](message)
                        except Exception as e:
                            print(f"Handler error: {e}")
                    
                    return True
                return False
            else:
                for agent_id, queue in self._message_queue.items():
                    if agent_id != message.from_agent:
                        if message.message_type in self._subscriptions.get(agent_id, []):
                            queue.append(message)
                            self._trim_queue(agent_id)
                            
                            if agent_id in self._message_handlers:
                                try:
                                    await self._message_handlers[agent_id](message)
                                except Exception:
                                    pass
                
                return True
    
    async def get_messages(self, agent_id: str, 
                          message_types: Optional[List[MessageType]] = None,
                          min_priority: Optional[Priority] = None,
                          limit: int = 50,
                          unread_only: bool = False) -> List[AgentMessage]:
        """Get pending messages for an agent
        
        Args:
            agent_id: The agent to get messages for
            message_types: Optional filter by message types
            min_priority: Optional minimum priority filter
            limit: Maximum number of messages to return
            unread_only: If True, only return unacknowledged messages
        """
        async with self._lock:
            if agent_id not in self._message_queue:
                return []
            
            messages = self._message_queue[agent_id].copy()
            
            if unread_only:
                messages = [m for m in messages if not m.ack_received]
            
            if message_types:
                messages = [m for m in messages if m.message_type in message_types]
            
            if min_priority:
                messages = [m for m in messages if m.priority.value >= min_priority.value]
            
            messages.sort(key=lambda m: (-m.priority.value, m.timestamp))
            
            return messages[:limit]
    
    async def acknowledge_message(self, agent_id: str, message_id: str):
        """Acknowledge receipt of a message"""
        async with self._lock:
            if agent_id in self._message_queue:
                for msg in self._message_queue[agent_id]:
                    if msg.id == message_id:
                        msg.ack_received = True
                        break
    
    async def clear_messages(self, agent_id: str, message_ids: Optional[List[str]] = None):
        """Clear messages from agent's queue"""
        async with self._lock:
            if agent_id in self._message_queue:
                if message_ids:
                    self._message_queue[agent_id] = [
                        m for m in self._message_queue[agent_id]
                        if m.id not in message_ids
                    ]
                else:
                    self._message_queue[agent_id] = []
    
    def set_message_handler(self, agent_id: str, handler: Callable):
        """Set a real-time message handler for an agent"""
        self._message_handlers[agent_id] = handler
    
    async def share_discovery(self, agent_id: str, discovery_type: str, 
                             key: str, data: Any, broadcast: bool = True) -> bool:
        """Share a discovery with other agents"""
        discovery_key = f"{discovery_type}:{key}"
        
        async with self._lock:
            if discovery_key in self._shared_discoveries:
                return False
            
            self._shared_discoveries[discovery_key] = {
                "agent_id": agent_id,
                "type": discovery_type,
                "key": key,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            self._trim_discoveries()
        
        if broadcast:
            message = AgentMessage(
                id="",
                from_agent=agent_id,
                to_agent=None,
                message_type=MessageType.DISCOVERY,
                content={
                    "discovery_type": discovery_type,
                    "key": key,
                    "data": data
                },
                priority=Priority.NORMAL
            )
            await self.send_message(message)
        
        return True
    
    async def get_discoveries(self, discovery_type: Optional[str] = None) -> List[Dict]:
        """Get shared discoveries"""
        async with self._lock:
            discoveries = list(self._shared_discoveries.values())
            
            if discovery_type:
                discoveries = [d for d in discoveries if d["type"] == discovery_type]
            
            return discoveries
    
    async def check_if_discovered(self, discovery_type: str, key: str) -> bool:
        """Check if something has already been discovered"""
        discovery_key = f"{discovery_type}:{key}"
        return discovery_key in self._shared_discoveries
    
    async def share_finding(self, agent_id: str, finding: Dict):
        """Share a security finding with all agents"""
        message = AgentMessage(
            id="",
            from_agent=agent_id,
            to_agent=None,
            message_type=MessageType.FINDING,
            content=finding,
            priority=Priority.HIGH if finding.get("severity") in ["Critical", "High"] else Priority.NORMAL
        )
        await self.send_message(message)
    
    async def request_help(self, agent_id: str, task_type: str, 
                          task_description: str, requirements: Optional[Dict] = None) -> str:
        """Request help from other agents"""
        message = AgentMessage(
            id="",
            from_agent=agent_id,
            to_agent=None,
            message_type=MessageType.REQUEST_HELP,
            content={
                "task_type": task_type,
                "description": task_description,
                "requirements": requirements or {},
                "requesting_agent": agent_id
            },
            priority=Priority.HIGH,
            requires_ack=True
        )
        await self.send_message(message)
        return message.id
    
    async def offer_help(self, from_agent: str, to_agent: str, 
                        help_request_id: str, capabilities: List[str]):
        """Offer to help another agent"""
        message = AgentMessage(
            id="",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.OFFER_HELP,
            content={
                "request_id": help_request_id,
                "capabilities": capabilities,
                "helper_agent": from_agent
            },
            priority=Priority.NORMAL
        )
        await self.send_message(message)
    
    async def claim_task(self, agent_id: str, task_identifier: str) -> bool:
        """Claim a task to prevent duplicate work"""
        async with self._lock:
            if task_identifier in self._completed_tasks:
                return False
            
            if task_identifier in self._in_progress_tasks:
                return False
            
            self._in_progress_tasks[task_identifier] = agent_id
            
        message = AgentMessage(
            id="",
            from_agent=agent_id,
            to_agent=None,
            message_type=MessageType.COORDINATION,
            content={
                "action": "task_claimed",
                "task": task_identifier
            },
            priority=Priority.NORMAL
        )
        await self.send_message(message)
        
        return True
    
    async def complete_task(self, agent_id: str, task_identifier: str, result: Any = None):
        """Mark a task as complete"""
        async with self._lock:
            if task_identifier in self._in_progress_tasks:
                del self._in_progress_tasks[task_identifier]
            self._completed_tasks.add(task_identifier)
            self._trim_completed_tasks()
        
        message = AgentMessage(
            id="",
            from_agent=agent_id,
            to_agent=None,
            message_type=MessageType.TASK_COMPLETION,
            content={
                "task": task_identifier,
                "result": result
            },
            priority=Priority.NORMAL
        )
        await self.send_message(message)
    
    async def is_task_available(self, task_identifier: str) -> bool:
        """Check if a task is available (not claimed or completed)"""
        async with self._lock:
            return (task_identifier not in self._completed_tasks and 
                    task_identifier not in self._in_progress_tasks)
    
    async def get_available_agents(self, specialization: Optional[str] = None) -> List[AgentCapability]:
        """Get list of available agents, optionally filtered by specialization"""
        async with self._lock:
            agents = list(self._agent_capabilities.values())
            
            agents = [a for a in agents if a.status in ["running", "idle"]]
            
            if specialization:
                agents = [a for a in agents 
                         if specialization in a.specializations]
            
            agents.sort(key=lambda a: a.current_load)
            
            return agents
    
    async def find_best_agent_for_task(self, task_type: str, 
                                       exclude_agent: Optional[str] = None) -> Optional[str]:
        """Find the best available agent for a specific task type"""
        specialization_map = {
            "port_scan": ["network_recon", "scanning"],
            "web_vuln": ["web_scanning", "vuln_scanning"],
            "exploitation": ["exploitation", "post_exploitation"],
            "recon": ["network_recon", "osint"],
            "enumeration": ["enumeration", "web_scanning"]
        }
        
        required_specs = specialization_map.get(task_type, [])
        
        available = await self.get_available_agents()
        available = [a for a in available if a.agent_id != exclude_agent]
        
        if required_specs:
            matching = [a for a in available 
                       if any(s in a.specializations for s in required_specs)]
            if matching:
                return matching[0].agent_id
        
        if available:
            return available[0].agent_id
        
        return None
    
    async def broadcast_alert(self, agent_id: str, alert_type: str, 
                             message: str, data: Optional[Dict] = None):
        """Broadcast an alert to all agents"""
        msg = AgentMessage(
            id="",
            from_agent=agent_id,
            to_agent=None,
            message_type=MessageType.ALERT,
            content={
                "alert_type": alert_type,
                "message": message,
                "data": data or {}
            },
            priority=Priority.CRITICAL
        )
        await self.send_message(msg)
    
    async def get_team_status(self) -> Dict:
        """Get status overview of all agents"""
        async with self._lock:
            return {
                "total_agents": len(self._agent_capabilities),
                "agents": {
                    agent_id: {
                        "status": cap.status,
                        "load": cap.current_load,
                        "target": cap.target,
                        "findings": cap.findings_count,
                        "specializations": cap.specializations
                    }
                    for agent_id, cap in self._agent_capabilities.items()
                },
                "total_discoveries": len(self._shared_discoveries),
                "tasks_in_progress": len(self._in_progress_tasks),
                "tasks_completed": len(self._completed_tasks)
            }
    
    def get_statistics(self) -> Dict:
        """Get communication statistics"""
        total_messages = sum(len(q) for q in self._message_queue.values())
        
        return {
            "registered_agents": len(self._agent_capabilities),
            "pending_messages": total_messages,
            "shared_discoveries": len(self._shared_discoveries),
            "completed_tasks": len(self._completed_tasks),
            "in_progress_tasks": len(self._in_progress_tasks),
            "message_counter": self._message_counter
        }


class KnowledgeBase:
    """
    Shared Knowledge Base for Agent Collaboration
    
    Stores and manages:
    - Discovered ports and services
    - Identified technologies
    - Found vulnerabilities
    - Attack paths
    - Credentials (hashed)
    """
    
    def __init__(self):
        self._knowledge: Dict[str, Any] = {
            "ports": {},
            "services": {},
            "technologies": {},
            "vulnerabilities": {},
            "directories": {},
            "subdomains": {},
            "credentials": {},
            "attack_paths": [],
            "recommendations": []
        }
        self._lock = asyncio.Lock()
    
    async def add_port(self, target: str, port: int, service: Optional[str] = None, 
                      version: Optional[str] = None, agent_id: Optional[str] = None):
        """Add discovered port information"""
        async with self._lock:
            key = f"{target}:{port}"
            if key not in self._knowledge["ports"]:
                self._knowledge["ports"][key] = {
                    "target": target,
                    "port": port,
                    "service": service,
                    "version": version,
                    "discovered_by": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def add_technology(self, target: str, tech_name: str, 
                            version: Optional[str] = None, agent_id: Optional[str] = None):
        """Add discovered technology"""
        async with self._lock:
            key = f"{target}:{tech_name}"
            if key not in self._knowledge["technologies"]:
                self._knowledge["technologies"][key] = {
                    "target": target,
                    "technology": tech_name,
                    "version": version,
                    "discovered_by": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def add_vulnerability(self, target: str, vuln_type: str, 
                               details: str, severity: str = "Medium",
                               cve: Optional[str] = None, agent_id: Optional[str] = None):
        """Add discovered vulnerability"""
        async with self._lock:
            key = f"{target}:{vuln_type}:{hash(details) % 10000}"
            if key not in self._knowledge["vulnerabilities"]:
                self._knowledge["vulnerabilities"][key] = {
                    "target": target,
                    "type": vuln_type,
                    "details": details,
                    "severity": severity,
                    "cve": cve,
                    "discovered_by": agent_id,
                    "verified": False,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def add_subdomain(self, parent_domain: str, subdomain: str, 
                           ip: Optional[str] = None, agent_id: Optional[str] = None):
        """Add discovered subdomain"""
        async with self._lock:
            if subdomain not in self._knowledge["subdomains"]:
                self._knowledge["subdomains"][subdomain] = {
                    "parent": parent_domain,
                    "subdomain": subdomain,
                    "ip": ip,
                    "discovered_by": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def add_directory(self, target: str, path: str, 
                           status_code: Optional[int] = None, agent_id: Optional[str] = None):
        """Add discovered directory/path"""
        async with self._lock:
            key = f"{target}{path}"
            if key not in self._knowledge["directories"]:
                self._knowledge["directories"][key] = {
                    "target": target,
                    "path": path,
                    "status_code": status_code,
                    "discovered_by": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def get_knowledge(self, category: Optional[str] = None) -> Dict:
        """Get knowledge, optionally filtered by category"""
        async with self._lock:
            if category:
                return self._knowledge.get(category, {})
            return self._knowledge.copy()
    
    async def get_target_summary(self, target: str) -> Dict:
        """Get all knowledge about a specific target"""
        async with self._lock:
            summary = {
                "ports": [],
                "technologies": [],
                "vulnerabilities": [],
                "directories": [],
                "subdomains": []
            }
            
            for key, data in self._knowledge["ports"].items():
                if target in key:
                    summary["ports"].append(data)
            
            for key, data in self._knowledge["technologies"].items():
                if target in key:
                    summary["technologies"].append(data)
            
            for key, data in self._knowledge["vulnerabilities"].items():
                if target in key:
                    summary["vulnerabilities"].append(data)
            
            for key, data in self._knowledge["directories"].items():
                if target in key:
                    summary["directories"].append(data)
            
            for subdomain, data in self._knowledge["subdomains"].items():
                if target in data.get("parent", ""):
                    summary["subdomains"].append(data)
            
            return summary
    
    async def check_if_scanned(self, target: str, port: Optional[int] = None, 
                              scan_type: Optional[str] = None) -> bool:
        """Check if a target/port has already been scanned"""
        async with self._lock:
            if port:
                key = f"{target}:{port}"
                return key in self._knowledge["ports"]
            
            for key in self._knowledge["ports"]:
                if target in key:
                    return True
            
            return False
    
    async def export_to_json(self) -> str:
        """Export knowledge base to JSON"""
        async with self._lock:
            return json.dumps(self._knowledge, indent=2, default=str)
    
    async def import_from_json(self, json_data: str):
        """Import knowledge base from JSON"""
        async with self._lock:
            data = json.loads(json_data)
            for category, items in data.items():
                if category in self._knowledge:
                    self._knowledge[category].update(items)


agent_comm = InterAgentCommunication()
knowledge_base = KnowledgeBase()
