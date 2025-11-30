import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from agent.executor import CommandExecutor
from models.router import ModelRouter
from monitor.log import Logger
from tools import is_tool_allowed, is_dangerous_command, get_allowed_tools_by_category
import re
import json

from agent.memory import get_memory, AgentMemory
from agent.throttle import IntelligentThrottler, RateLimiter, ThrottleLevel
from agent.collaboration import (
    InterAgentCommunication, KnowledgeBase, AgentCapability, 
    MessageType, Priority, AgentMessage
)
import threading

_shared_throttler = None
_shared_rate_limiter = None
_shared_agent_comm = None
_shared_knowledge_base = None
_init_lock = threading.Lock()

def _get_shared_instances():
    """Get or create shared instances with proper thread-safe locking"""
    global _shared_throttler, _shared_rate_limiter, _shared_agent_comm, _shared_knowledge_base
    
    if _shared_throttler is not None:
        return _shared_throttler, _shared_rate_limiter, _shared_agent_comm, _shared_knowledge_base
    
    with _init_lock:
        if _shared_throttler is None:
            _shared_throttler = IntelligentThrottler()
            _shared_rate_limiter = RateLimiter()
            _shared_agent_comm = InterAgentCommunication()
            _shared_knowledge_base = KnowledgeBase()
    
    return _shared_throttler, _shared_rate_limiter, _shared_agent_comm, _shared_knowledge_base

try:
    import psutil
    PSUTIL_AVAILABLE = True
    psutil.cpu_percent(interval=None)
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

class AgentWorker:
    """Individual autonomous agent worker with SQLite memory, intelligent throttling, and collaboration"""
    
    def __init__(
        self,
        agent_id: str,
        agent_number: int,
        target: str,
        category: str,
        custom_instruction: Optional[str],
        stealth_mode: bool,
        aggressive_mode: bool,
        model_name: str,
        shared_knowledge: Dict,
        logger: Logger,
        stealth_config: Optional[Dict] = None,
        os_type: str = "linux",
        stealth_options: Optional[Dict] = None,
        capabilities: Optional[Dict] = None,
        batch_size: int = 20,
        rate_limit_rps: float = 1.0,
        execution_duration: Optional[int] = None,
        requested_tools: Optional[List[str]] = None,
        allowed_tools_only: bool = False
    ):
        self.agent_id = agent_id
        self.agent_number = agent_number
        self.target = target
        self.category = category
        self.custom_instruction = custom_instruction
        self.stealth_mode = stealth_mode
        self.aggressive_mode = aggressive_mode
        self.model_name = model_name
        self.shared_knowledge = shared_knowledge
        self.logger = logger
        self.os_type = os_type
        self.stealth_options = stealth_options or {}
        self.capabilities = capabilities or {}
        
        self.batch_size = batch_size
        self.rate_limit_rps = rate_limit_rps
        self.execution_duration = execution_duration
        self.requested_tools = requested_tools or []
        self.allowed_tools_only = allowed_tools_only
        self.execution_start_time: Optional[datetime] = None
        self.break_reason: Optional[str] = None
        
        self.executor = CommandExecutor(agent_id, stealth_mode, stealth_config, target, os_type)
        self.model_router = ModelRouter()
        
        self.status = "idle"
        self.start_time = None
        self.last_execute = "Not started"
        self.execution_history: List[Dict] = []
        self.context_history: List[Dict] = []
        self.instruction_history: List[Dict] = []
        self.paused = False
        self.stopped = False
        
        self._last_cpu_usage: Optional[float] = None
        self._last_memory_usage: Optional[int] = None
        
        self._max_context_history = 4
        self._max_execution_history = 8
        self._max_instruction_history = 6
        self._gc_counter = 0
        self._gc_interval = 3
        self._lazy_init_done = False
        
        self.memory: AgentMemory = get_memory()
        throttler, rate_limiter, agent_comm, knowledge_base = _get_shared_instances()
        self.throttler = throttler
        self.rate_limiter = rate_limiter
        self.agent_comm = agent_comm
        self.knowledge_base = knowledge_base
        
        self._specializations = self._determine_specializations()
        
    def _determine_specializations(self) -> List[str]:
        """Determine agent specializations based on category and capabilities"""
        spec_map = {
            "domain": ["network_recon", "osint", "subdomain_enum"],
            "ip": ["network_recon", "port_scanning", "service_enum"],
            "url": ["web_scanning", "vuln_scanning", "directory_enum"],
            "file": ["static_analysis", "code_review"]
        }
        return spec_map.get(self.category, ["general"])
    
    def _trim_memory(self):
        """Trim in-memory lists to prevent memory buildup - keeps agent lightweight"""
        import gc
        
        if len(self.context_history) > self._max_context_history:
            excess = len(self.context_history) - self._max_context_history
            del self.context_history[:excess]
        
        if len(self.execution_history) > self._max_execution_history:
            excess = len(self.execution_history) - self._max_execution_history
            del self.execution_history[:excess]
        
        if len(self.instruction_history) > self._max_instruction_history:
            excess = len(self.instruction_history) - self._max_instruction_history
            del self.instruction_history[:excess]
        
        for item in self.context_history:
            if isinstance(item.get("content"), str) and len(item["content"]) > 1500:
                item["content"] = item["content"][:1500] + "..."
        
        for item in self.execution_history:
            if isinstance(item.get("result"), str) and len(item["result"]) > 800:
                item["result"] = item["result"][:800] + "..."
        
        self._gc_counter += 1
        if self._gc_counter >= self._gc_interval:
            gc.collect(generation=0)
            self._gc_counter = 0
    
    def _cleanup_on_complete(self):
        """Clean up memory when agent completes - free up resources"""
        import gc
        
        self.context_history.clear()
        self.execution_history = self.execution_history[-3:]
        self.instruction_history = self.instruction_history[-3:]
        
        self.throttler.unregister_agent(self.agent_id)
        
        gc.collect()
        
    async def start(self):
        """Start agent execution with memory, throttling, and collaboration initialization"""
        self.status = "running"
        self.start_time = time.time()
        
        await self._initialize_systems()
        
        await self.logger.log_event(
            f"Agent {self.agent_id} started",
            "agent",
            {"agent_number": self.agent_number, "target": self.target or "no target"}
        )
        
        if not self.target:
            self.last_execute = "Agent ready, awaiting target assignment"
            self.status = "idle"
            await self.logger.log_event(
                f"Agent {self.agent_id} running in standby mode (no target)",
                "agent",
                {"agent_id": self.agent_id}
            )
            await self._broadcast_status_update()
            return
        
        self.last_execute = f"Initializing analysis of {self.target}..."
        await self._broadcast_status_update()
        
        try:
            await self._run_autonomous_loop()
        except Exception as e:
            self.status = "error"
            self.last_execute = f"Error: {str(e)[:100]}"
            await self.logger.log_event(
                f"Agent {self.agent_id} error: {str(e)}",
                "error",
                {"agent_id": self.agent_id}
            )
            await self._broadcast_status_update()
        finally:
            await self.memory.update_agent_status(self.agent_id, self.status)
    
    async def _initialize_systems(self):
        """Initialize memory, throttling, and collaboration systems"""
        await self.memory.initialize()
        await self.memory.register_agent(
            agent_id=self.agent_id,
            agent_number=self.agent_number,
            target=self.target,
            category=self.category,
            model_name=self.model_name,
            metadata={
                "stealth_mode": self.stealth_mode,
                "aggressive_mode": self.aggressive_mode,
                "specializations": self._specializations
            }
        )
        
        self.throttler.register_agent(self.agent_id, base_delay=1.5 if self.stealth_mode else 1.0)
        
        capability = AgentCapability(
            agent_id=self.agent_id,
            specializations=self._specializations,
            current_load=0.0,
            status="running",
            target=self.target,
            tools_available=list(get_allowed_tools_by_category().keys()),
            findings_count=0
        )
        await self.agent_comm.register_agent(self.agent_id, capability)
        
        self.agent_comm.set_message_handler(self.agent_id, self._handle_agent_message)
        
        await self.logger.log_event(
            f"Agent {self.agent_id} systems initialized",
            "system",
            {"memory": True, "throttler": True, "collaboration": True}
        )
    
    async def _handle_agent_message(self, message: AgentMessage):
        """Handle incoming messages from other agents"""
        if message.message_type == MessageType.DISCOVERY:
            discovery = message.content
            await self.memory.add_knowledge(
                agent_id=message.from_agent,
                knowledge_type=discovery.get("discovery_type", "general"),
                key=discovery.get("key", ""),
                value=discovery.get("data", {}),
                source=f"agent:{message.from_agent}"
            )
        
        elif message.message_type == MessageType.FINDING:
            finding = message.content
            await self.logger.log_event(
                f"Received finding from {message.from_agent}: {finding.get('content', '')[:100]}",
                "collaboration"
            )
        
        elif message.message_type == MessageType.REQUEST_HELP:
            can_help = any(
                spec in self._specializations 
                for spec in message.content.get("requirements", {}).get("specializations", [])
            )
            if can_help and self.status in ["running", "idle"]:
                await self.agent_comm.offer_help(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    help_request_id=message.id,
                    capabilities=self._specializations
                )
        
        elif message.message_type == MessageType.ALERT:
            await self.logger.log_event(
                f"ALERT from {message.from_agent}: {message.content.get('message', '')}",
                "alert",
                message.content
            )
    
    async def _broadcast_status_update(self):
        """Broadcast current status to WebSocket clients - optimized version"""
        try:
            from server.ws import manager
            
            exec_time = self._get_execution_time_str()
            progress = min(100, len(self.execution_history) * 7 + 5)
            
            if PSUTIL_AVAILABLE and psutil:
                try:
                    self._last_cpu_usage = psutil.cpu_percent(interval=None)
                    mem = psutil.virtual_memory()
                    self._last_memory_usage = int(mem.used / 1024 / 1024)
                except:
                    pass
            
            message = {
                "type": "agent_status",
                "agent_id": self.agent_id,
                "status": self.status,
                "last_command": self.last_execute[:120] if self.last_execute else "",
                "execution_time": exec_time,
                "progress": progress
            }
            
            if self._last_cpu_usage is not None:
                message["cpu_usage"] = round(self._last_cpu_usage, 1)
            if self._last_memory_usage is not None:
                message["memory_usage"] = self._last_memory_usage
            if self.break_reason:
                message["break_reason"] = self.break_reason
            
            await manager.broadcast(message)
        except Exception:
            pass
    
    async def _set_break_status(self, reason: str):
        """Set agent to break status with reason"""
        self.status = "break"
        self.break_reason = reason
        await self._broadcast_status_update()
    
    async def _clear_break_status(self):
        """Clear break status and resume running"""
        self.status = "running"
        self.break_reason = None
        await self._broadcast_status_update()
    
    def _check_execution_duration_expired(self) -> bool:
        """Check if execution duration has expired"""
        if not self.execution_duration or not self.execution_start_time:
            return False
        elapsed_minutes = (datetime.now() - self.execution_start_time).total_seconds() / 60
        return elapsed_minutes >= self.execution_duration
    
    def _is_tool_allowed_by_user(self, cmd: str) -> bool:
        """Check if tool is allowed based on user selection"""
        if not self.allowed_tools_only or not self.requested_tools:
            return True
        tool = cmd.split()[0] if cmd else ""
        if tool.startswith("RUN "):
            tool = tool[4:].split()[0]
        return tool.lower() in [t.lower() for t in self.requested_tools]
    
    def _get_execution_time_str(self) -> str:
        """Get formatted execution time string"""
        if not self.start_time:
            return "00:00"
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins:02d}:{secs:02d}"
    
    async def _broadcast_queue_update(self):
        """Broadcast shared queue state to WebSocket clients"""
        try:
            from server.ws import manager
            from agent.shared_queue import get_shared_queue
            shared_queue = get_shared_queue()
            queue_state = await shared_queue.get_queue_state()
            
            await manager.broadcast({
                "type": "queue_update",
                "queue": queue_state,
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass
    
    async def _run_autonomous_loop(self):
        """Main autonomous execution loop - uses shared queue for token efficiency"""
        
        self.execution_start_time = datetime.now()
        system_prompt = self._build_system_prompt()
        
        iteration = 0
        max_iterations = 50
        
        self.last_execute = f"Starting security analysis of {self.target}..."
        await self._broadcast_status_update()
        
        from agent.shared_queue import get_shared_queue
        shared_queue = get_shared_queue()
        
        while not self.stopped and iteration < max_iterations:
            if self._check_execution_duration_expired():
                self.last_execute = f"Execution duration ({self.execution_duration}min) reached - stopping"
                self.status = "completed"
                await self.logger.log_event(
                    f"Agent {self.agent_id} stopped - execution duration expired",
                    "agent",
                    {"duration_minutes": self.execution_duration}
                )
                await self._broadcast_status_update()
                break
            
            while self.paused and not self.stopped:
                self.last_execute = "Agent paused"
                await asyncio.sleep(1)
            
            if self.stopped:
                break
            
            instruction = await shared_queue.claim_next(self.agent_id)
            if instruction:
                cmd = instruction.get("command", "")
                instruction_id = instruction.get("id")
                if cmd.startswith("RUN "):
                    if not self._is_tool_allowed_by_user(cmd):
                        tool_name = cmd[4:].split()[0] if len(cmd) > 4 else "unknown"
                        self.last_execute = f"BLOCKED: Tool '{tool_name}' not in allowed list"
                        await shared_queue.fail_instruction(instruction_id, self.agent_id, f"Tool {tool_name} not allowed by user")
                        await self._broadcast_status_update()
                        continue
                    
                    self.last_execute = f"Executing: {cmd[4:50]}..."
                    await self._broadcast_status_update()
                    try:
                        await self._execute_single_command(cmd)
                        await shared_queue.complete_instruction(instruction_id, self.agent_id, "completed")
                    except Exception as e:
                        await shared_queue.fail_instruction(instruction_id, self.agent_id, str(e))
                    await self._broadcast_status_update()
                continue
            
            iteration += 1
            if iteration >= max_iterations:
                self.last_execute = f"Completed {iteration} analysis iterations"
                self.status = "completed"
                await self._broadcast_status_update()
                break
            
            await self._set_break_status("Waiting for model response...")
            self.last_execute = f"Iteration {iteration}: Requesting instructions..."
            
            user_message = self._build_user_message(iteration)
            
            try:
                rate_limit_check = await self.rate_limiter.acquire(
                    self.model_name, 
                    estimated_tokens=2000
                )
                
                if rate_limit_check.get("wait_time", 0) > 0:
                    wait_time = rate_limit_check["wait_time"]
                    await self._set_break_status(f"Rate limit delay: {wait_time:.1f}s")
                    self.last_execute = f"Rate limit delay: {wait_time:.1f}s"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} rate limit delay",
                        "rate_limit",
                        {"model": self.model_name, "wait_time": wait_time}
                    )
                    await asyncio.sleep(wait_time)
                
                start_time = time.time()
                response = await self.model_router.generate(
                    self.model_name,
                    system_prompt,
                    user_message,
                    self.context_history[-self._max_context_history:]
                )
                execution_time = time.time() - start_time
                
                await self._clear_break_status()
                
                await self.rate_limiter.record_request(
                    self.model_name, 
                    tokens_used=len(response) // 4,
                    success=True
                )
                
                await self.memory.save_conversation(
                    self.agent_id, "user", user_message, iteration
                )
                await self.memory.save_conversation(
                    self.agent_id, "assistant", response, iteration
                )
                
                response_summary = response[:100].replace('\n', ' ')
                self.last_execute = f"AI: {response_summary}..."
                
                await self._broadcast_model_instruction(response)
                await self._broadcast_status_update()
                
                self.context_history.append({
                    "role": "user",
                    "content": user_message[:2000]
                })
                self.context_history.append({
                    "role": "assistant",
                    "content": response[:3000]
                })
                
                self._trim_memory()
                
                if "<END!>" in response or '"status": "END"' in response or '"status":"END"' in response:
                    self.last_execute = "Mission completed successfully"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} completed mission",
                        "agent"
                    )
                    self.status = "completed"
                    await self._broadcast_status_update()
                    break
                
                commands = self._extract_commands(response)
                
                if commands:
                    self._save_instruction_to_history(response, commands)
                    cmd_list = list(commands.values())
                    added_count = await shared_queue.add_instructions(cmd_list)
                    await self._broadcast_event("model_output", f"Model queued {added_count} commands to shared queue")
                    await self._broadcast_queue_update()
                    await self.logger.log_event(
                        f"Agent {self.agent_id} added {added_count} commands to shared queue",
                        "command",
                        {"commands": added_count}
                    )
                
                json_findings = self._extract_findings_from_json(response)
                if json_findings:
                    for jf in json_findings:
                        if isinstance(jf, dict):
                            content = jf.get("content", "")
                            severity = jf.get("severity", "Info")
                            if content:
                                await self._save_single_finding(content, severity)
                
                findings = self._extract_findings(response)
                
                if findings:
                    await self._save_findings_with_sharing(findings)
                
                await self._share_knowledge(response)
                
                await asyncio.sleep(2.0)
                
            except Exception as e:
                error_str = str(e)
                self.last_execute = f"Error: {error_str[:80]}"
                
                if "rate" in error_str.lower() or "429" in error_str:
                    cooldown = await self.rate_limiter.handle_rate_limit_error(self.model_name)
                    self.last_execute = f"Rate limit hit, cooling down {cooldown['cooldown_seconds']}s"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} rate limit error",
                        "rate_limit",
                        cooldown
                    )
                    await asyncio.sleep(cooldown['cooldown_seconds'])
                    continue
                
                await self.rate_limiter.record_request(self.model_name, success=False)
                
                await self.logger.log_event(
                    f"Agent {self.agent_id} iteration error: {error_str}",
                    "error",
                    {"error_type": type(e).__name__, "model": self.model_name}
                )
                await self._broadcast_status_update()
                
                if "401" in error_str and "Unauthorized" in error_str:
                    self.status = "error"
                    self.last_execute = f"Auth Error: {error_str[:60]}"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} stopping due to auth error: {error_str}",
                        "error"
                    )
                    await self._broadcast_status_update()
                    break
                
                await asyncio.sleep(3)
        
        if iteration >= max_iterations:
            self.status = "completed"
            self.last_execute = "Reached maximum iterations"
            await self.logger.log_event(
                f"Agent {self.agent_id} reached max iterations",
                "agent"
            )
        
        self.status = "completed"
        await self._broadcast_status_update()
        
        self._cleanup_on_complete()
    
    async def _build_user_message_with_collaboration(self, iteration: int) -> str:
        """Build user message with collaboration data from other agents"""
        messages = await self.agent_comm.get_messages(
            self.agent_id, 
            unread_only=True, 
            limit=10
        )
        
        knowledge = await self.knowledge_base.get_target_summary(self.target)
        
        message = f"Iteration {iteration}:\n\n"
        
        if messages:
            message += "## Messages from other agents:\n"
            for msg in messages[:5]:
                msg_type = msg.message_type.value if hasattr(msg.message_type, 'value') else msg.message_type
                message += f"- [{msg.from_agent}] ({msg_type}): {str(msg.content)[:150]}\n"
            message += "\n"
            
            await self.agent_comm.clear_messages(
                self.agent_id, 
                [m.id for m in messages[:5]]
            )
        
        if knowledge.get("ports"):
            message += f"## Known open ports: {len(knowledge['ports'])} discovered\n"
            for port_info in knowledge["ports"][:5]:
                message += f"- Port {port_info.get('port')}: {port_info.get('service', 'unknown')}\n"
            message += "\n"
        
        if knowledge.get("vulnerabilities"):
            message += f"## Known vulnerabilities: {len(knowledge['vulnerabilities'])} found\n"
            for vuln in knowledge["vulnerabilities"][:3]:
                message += f"- [{vuln.get('severity')}] {vuln.get('type')}: {vuln.get('details', '')[:80]}\n"
            message += "\n"
        
        if self.execution_history:
            last_execution = self.execution_history[-1]
            message += f"## Last command executed:\n{last_execution.get('command')}\n"
            result_preview = last_execution.get('result', '')[:500]
            message += f"Result: {result_preview}...\n\n"
        
        message += "What is your next action? Provide commands to execute or signal completion with <END!>"
        
        return message
    
    async def _execute_commands_with_coordination(self, commands: Dict[str, str]):
        """Execute commands with coordination to avoid duplicate work"""
        for key, command in commands.items():
            if command.startswith("RUN "):
                cmd = command[4:].strip()
                
                task_id = f"{self.target}:{cmd.split()[0]}:{hash(cmd) % 10000}"
                
                is_available = await self.agent_comm.is_task_available(task_id)
                if not is_available:
                    self.last_execute = f"Skipped (already done by team): {cmd[:50]}"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} skipped duplicate task",
                        "coordination",
                        {"command": cmd[:100]}
                    )
                    continue
                
                claimed = await self.agent_comm.claim_task(self.agent_id, task_id)
                if not claimed:
                    self.last_execute = f"Task claimed by another agent: {cmd[:50]}"
                    continue
                
                if is_dangerous_command(cmd):
                    self.last_execute = f"BLOCKED: Dangerous command detected"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} blocked dangerous command: {cmd}",
                        "security_violation"
                    )
                    await self.agent_comm.complete_task(self.agent_id, task_id, {"blocked": True})
                    continue
                
                if not is_tool_allowed(cmd):
                    tool_name = cmd.split()[0]
                    self.last_execute = f"BLOCKED: Tool '{tool_name}' not in allowed list"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} blocked unauthorized tool: {tool_name}",
                        "security_violation"
                    )
                    await self.agent_comm.complete_task(self.agent_id, task_id, {"blocked": True})
                    continue
                
                if self.allowed_tools_only and self.requested_tools:
                    tool_name = cmd.split()[0]
                    if tool_name not in self.requested_tools:
                        self.last_execute = f"BLOCKED: Tool '{tool_name}' not in user-selected tools"
                        await self.logger.log_agent_event(
                            self.agent_id,
                            f"Blocked tool '{tool_name}' - not in user-selected tools: {self.requested_tools[:5]}",
                            "tool_restriction"
                        )
                        await self.agent_comm.complete_task(self.agent_id, task_id, {"blocked": True, "reason": "not_in_user_tools"})
                        continue
                
                self.last_execute = cmd
                
                await self.logger.log_event(
                    f"Agent {self.agent_id} executing: {cmd}",
                    "command"
                )
                
                start_time = time.time()
                result = await self.executor.execute(cmd)
                exec_time = time.time() - start_time
                
                await self.memory.save_execution(
                    self.agent_id, cmd, result, 
                    success=True, execution_time=exec_time
                )
                
                self.execution_history.append({
                    "command": cmd,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                await self._extract_and_share_discoveries(cmd, result)
                
                await self.agent_comm.complete_task(self.agent_id, task_id, {
                    "command": cmd,
                    "result_length": len(result)
                })
                
                await self.logger.log_event(
                    f"Agent {self.agent_id} completed: {cmd}",
                    "command",
                    {"result_length": len(result), "exec_time": exec_time}
                )
    
    async def _extract_and_share_discoveries(self, command: str, result: str):
        """Extract discoveries from command results and share with team"""
        import re
        
        if "nmap" in command.lower():
            port_pattern = r'(\d+)/(?:tcp|udp)\s+open\s+(\S+)'
            for match in re.finditer(port_pattern, result):
                port, service = match.groups()
                added = await self.knowledge_base.add_port(
                    self.target, int(port), service, agent_id=self.agent_id
                )
                if added:
                    await self.agent_comm.share_discovery(
                        self.agent_id,
                        "port",
                        f"{self.target}:{port}",
                        {"port": port, "service": service}
                    )
        
        if any(tool in command.lower() for tool in ["gobuster", "dirb", "ffuf"]):
            path_pattern = r'(/\S+)\s+\(Status:\s*(\d+)'
            for match in re.finditer(path_pattern, result):
                path, status = match.groups()
                await self.knowledge_base.add_directory(
                    self.target, path, int(status), agent_id=self.agent_id
                )
        
        if any(tool in command.lower() for tool in ["subfinder", "amass"]):
            subdomain_pattern = r'([a-zA-Z0-9][-a-zA-Z0-9]*\.' + re.escape(self.target) + r')'
            for match in re.finditer(subdomain_pattern, result):
                subdomain = match.group(1)
                await self.knowledge_base.add_subdomain(
                    self.target, subdomain, agent_id=self.agent_id
                )
    
    async def _save_findings_with_sharing(self, findings: List[str]):
        """Save findings and share with other agents - broadcasts in real-time"""
        for finding in findings:
            severity = self._classify_severity(finding)
            
            finding_data = {
                "agent_id": self.agent_id,
                "agent_number": self.agent_number,
                "content": finding,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "target": self.target
            }
            
            self.shared_knowledge["findings"].append(finding_data)
            
            await self.memory.save_finding(
                self.agent_id, self.target, finding, 
                severity=severity, category=self.category
            )
            
            await self.agent_comm.share_finding(self.agent_id, finding_data)
            
            if severity in ["Critical", "High"]:
                await self.knowledge_base.add_vulnerability(
                    self.target, 
                    "discovered",
                    finding,
                    severity=severity,
                    agent_id=self.agent_id
                )
            
            await self.logger.write_finding(self.agent_id, finding, target=self.target, severity=severity)
            
            await self._broadcast_finding_realtime(finding_data)
            
            await self.agent_comm.update_capabilities(
                self.agent_id,
                findings_count=len([f for f in self.shared_knowledge.get("findings", []) 
                                   if f["agent_id"] == self.agent_id])
            )
    
    async def _broadcast_finding_realtime(self, finding_data: Dict):
        """Broadcast finding to WebSocket clients in real-time"""
        try:
            from server.ws import manager
            await manager.broadcast_finding(finding_data)
        except Exception:
            pass
    
    async def _apply_intelligent_delay(self):
        """Apply intelligent delay based on throttling, stealth, and rate limits"""
        from server.config import settings
        
        throttle_result = await self.throttler.check_and_throttle(self.agent_id)
        throttle_delay = throttle_result.get("delay", 1.0)
        
        rate_status = self.rate_limiter.get_status(self.model_name)
        rate_delay = rate_status.get("current_delay", 1.0)
        
        if self.stealth_mode:
            base_delay = random.uniform(
                settings.DEFAULT_DELAY_MIN * 2,
                settings.DEFAULT_DELAY_MAX * 3
            )
        else:
            base_delay = random.uniform(
                settings.DEFAULT_DELAY_MIN,
                settings.DEFAULT_DELAY_MAX
            )
        
        final_delay = max(base_delay, throttle_delay, rate_delay)
        
        jitter = random.uniform(-0.3, 0.3) * final_delay
        final_delay = max(0.5, final_delay + jitter)
        
        resources = throttle_result.get("resources", {})
        await self.memory.record_resource_usage(
            self.agent_id,
            cpu=resources.get("cpu_percent", 0),
            memory=resources.get("memory_percent", 0),
            throttle=(throttle_result.get("throttle_level", "NONE") != "NONE")
        )
        
        await asyncio.sleep(final_delay)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for AI model - outputs sequential queue commands"""
        
        mode_str = "Stealth (evade detection)" if self.stealth_mode else "Aggressive (thorough scanning)" if self.aggressive_mode else "Normal"
        
        custom_section = ""
        if self.custom_instruction:
            custom_section = f"\nCUSTOM: {self.custom_instruction}\n"
        
        if self.allowed_tools_only and self.requested_tools:
            tools_str = ", ".join(sorted(self.requested_tools)[:30])
            tools_warning = "\nIMPORTANT: You can ONLY use these exact tools. Any other tool will be BLOCKED."
        else:
            tools_by_category = get_allowed_tools_by_category()
            tools_list = []
            for category, tools in tools_by_category.items():
                tools_list.extend(list(tools)[:8])
            tools_str = ", ".join(sorted(set(tools_list))[:30])
            tools_warning = ""
        
        prompt = f"""You are an autonomous cybersecurity AI orchestrating multiple agents.

Target: {self.target}
Category: {self.category}
Mode: {mode_str}
{custom_section}
AVAILABLE TOOLS: {tools_str}{tools_warning}

## OUTPUT FORMAT - SEQUENTIAL QUEUE COMMANDS

You MUST respond with a JSON object containing 5-10 commands in a SHARED QUEUE.
Keys are the queue order (1, 2, 3...), values are commands starting with "RUN ".
Multiple agents will pick up commands from this queue - whoever finishes first gets the next one.

PREDICT 5-10 COMMANDS at once to save tokens and avoid rate limits!

Example response format:
```json
{{
  "1": "RUN nmap -sV -sC {self.target}",
  "2": "RUN nikto -h {self.target}",
  "3": "RUN gobuster dir -u http://{self.target} -w /usr/share/wordlists/dirb/common.txt",
  "4": "RUN subfinder -d {self.target}",
  "5": "RUN nuclei -u {self.target}",
  "6": "RUN whatweb {self.target}",
  "7": "RUN wafw00f {self.target}",
  "8": "RUN curl -I {self.target}"
}}
```

## FINDINGS FORMAT
To report findings, add a "findings" array:
```json
{{
  "1": "RUN command1",
  "2": "RUN command2",
  "findings": [
    {{"severity": "High", "content": "SQL Injection found at /login"}},
    {{"severity": "Medium", "content": "Missing X-Frame-Options header"}}
  ]
}}
```

## COMPLETION
When done, respond with:
```json
{{"status": "END", "summary": "Assessment complete"}}
```

## RULES
- Output ONLY valid JSON, no explanations or text
- Predict 5-10 commands per response to maximize efficiency
- Commands are added to a SHARED QUEUE - all agents pick from same queue
- First agent to finish their current command picks up the next one
- DO NOT include any text outside the JSON object
- Use only tools from AVAILABLE TOOLS list
"""
        
        return prompt
    
    async def _build_user_message_json(self, iteration: int) -> str:
        """Build user message with target-filtered context for JSON batch output"""
        
        target_findings = await self.memory.get_findings_for_target(self.target, limit=10)
        
        message = f'{{"iteration": {iteration}, "target": "{self.target}"'
        
        if target_findings:
            findings_json = []
            for f in target_findings[:5]:
                findings_json.append(f'{{"severity": "{f.get("severity", "Info")}", "content": "{str(f.get("content", ""))[:100]}"}}')
            message += f', "existing_findings": [{", ".join(findings_json)}]'
        
        if self.execution_history:
            last_exec = self.execution_history[-1]
            cmd = last_exec.get('command', '').replace('"', '\\"')[:80]
            result = last_exec.get('result', '').replace('"', '\\"').replace('\n', ' ')[:200]
            message += f', "last_command": "{cmd}", "last_result": "{result}"'
        
        message += '}'
        
        return message
    
    def _build_user_message(self, iteration: int) -> str:
        """Build user message for current iteration - simple format"""
        
        target_findings = [f for f in self.shared_knowledge.get("findings", []) 
                         if f.get("target") == self.target][-5:]
        
        message = f"Iteration {iteration} for target {self.target}:\n\n"
        
        if target_findings:
            message += "Target findings:\n"
            for finding in target_findings:
                message += f"- [{finding.get('severity', 'Info')}] {finding.get('content', '')[:80]}\n"
            message += "\n"
        
        if self.execution_history:
            last_execution = self.execution_history[-1]
            message += f"Last: {last_execution.get('command', '')[:80]}\n"
            message += f"Result: {last_execution.get('result', '')[:300]}\n\n"
        
        message += "Respond with JSON batch commands only."
        
        return message
    
    def _extract_commands(self, response: str) -> Dict[str, str]:
        """Extract RUN commands from JSON response - returns ALL commands for shared queue"""
        
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        try:
            data = json.loads(response_clean)
            
            if data.get("status") == "END":
                return {}
            
            all_commands = {}
            
            for key, value in data.items():
                if key.isdigit() and isinstance(value, str) and value.startswith("RUN "):
                    all_commands[key] = value
            
            if all_commands:
                return all_commands
            
            for batch_name in ["batch_1", "batch_2", "batch_3"]:
                batch = data.get(batch_name, {})
                if isinstance(batch, dict):
                    for agent_key, cmd in batch.items():
                        if isinstance(cmd, str) and cmd.startswith("RUN "):
                            cmd_num = len(all_commands) + 1
                            all_commands[str(cmd_num)] = cmd
            
            if all_commands:
                return all_commands
                
        except json.JSONDecodeError:
            pass
        
        run_pattern = r'RUN\s+(.+?)(?:\n|$|")'
        matches = re.findall(run_pattern, response)
        
        if matches:
            commands = {}
            for i, match in enumerate(matches[:10], 1):
                commands[str(i)] = f"RUN {match.strip()}"
            return commands
        
        return {}
    
    def _extract_findings_from_json(self, response: str) -> List[Dict]:
        """Extract findings from JSON response"""
        
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        try:
            data = json.loads(response_clean)
            findings = data.get("findings", [])
            if isinstance(findings, list):
                return findings
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _extract_findings(self, response: str) -> List[str]:
        """Extract findings marked with <write> tags"""
        
        pattern = r'<write>(.*?)</write>'
        matches = re.findall(pattern, response, re.DOTALL)
        
        return [m.strip() for m in matches]
    
    async def _execute_single_command(self, command: str):
        """Execute a single command from queue"""
        if not command.startswith("RUN "):
            return
        
        cmd = command[4:].strip()
        
        if is_dangerous_command(cmd):
            self.last_execute = f"BLOCKED: Dangerous command"
            await self._broadcast_event("info", f"BLOCKED: Dangerous command: {cmd[:50]}")
            return
        
        if not is_tool_allowed(cmd):
            tool_name = cmd.split()[0]
            self.last_execute = f"BLOCKED: Tool '{tool_name}' not allowed"
            await self._broadcast_event("info", f"BLOCKED: Tool '{tool_name}' not in allowed list")
            return
        
        self.last_execute = cmd
        await self._broadcast_event("execute", f"Executing: {cmd}")
        
        await self.logger.log_event(f"Agent {self.agent_id} executing: {cmd}", "command")
        
        result = await self.executor.execute(cmd)
        
        self.execution_history.append({
            "command": cmd,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        result_preview = result[:100].replace('\n', ' ') if result else "No output"
        await self._broadcast_event("info", f"Done: {cmd[:40]}... -> {result_preview}")
        
        await self.logger.log_event(
            f"Agent {self.agent_id} completed: {cmd}",
            "command",
            {"result_length": len(result)}
        )
    
    async def _execute_commands(self, commands: Dict[str, str]):
        """Execute extracted commands with validation"""
        
        for key, command in commands.items():
            if command.startswith("RUN "):
                cmd = command[4:].strip()
                
                if is_dangerous_command(cmd):
                    self.last_execute = f"BLOCKED: Dangerous command detected"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} blocked dangerous command: {cmd}",
                        "security_violation"
                    )
                    continue
                
                if not is_tool_allowed(cmd):
                    tool_name = cmd.split()[0]
                    self.last_execute = f"BLOCKED: Tool '{tool_name}' not in allowed list"
                    await self.logger.log_event(
                        f"Agent {self.agent_id} blocked unauthorized tool: {tool_name}",
                        "security_violation"
                    )
                    continue
                
                self.last_execute = cmd
                
                await self._broadcast_event("execute", f"Executing: {cmd}")
                
                await self.logger.log_event(
                    f"Agent {self.agent_id} executing: {cmd}",
                    "command"
                )
                
                result = await self.executor.execute(cmd)
                
                self.execution_history.append({
                    "command": cmd,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                result_preview = result[:150].replace('\n', ' ') if result else "No output"
                await self._broadcast_event("info", f"Completed: {cmd[:50]}... -> {result_preview}")
                
                await self.logger.log_event(
                    f"Agent {self.agent_id} completed: {cmd}",
                    "command",
                    {"result_length": len(result)}
                )
    
    async def _save_findings(self, findings: List[str]):
        """Save findings to log and shared knowledge"""
        import uuid
        
        for finding in findings:
            severity = self._classify_severity(finding)
            finding_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().isoformat()
            
            finding_data = {
                "agent_id": self.agent_id,
                "agent_number": self.agent_number,
                "content": finding,
                "severity": severity,
                "timestamp": timestamp,
                "target": self.target,
                "id": finding_id
            }
            
            self.shared_knowledge["findings"].append(finding_data)
            
            await self.logger.write_finding(self.agent_id, finding, target=self.target)
            
            await self._broadcast_event("found", finding, severity.lower())
            await self._broadcast_finding(finding_id, finding, severity, timestamp)
            
            await self.logger.log_event(
                f"Agent {self.agent_id} finding: {finding[:100]}...",
                "finding",
                {"severity": severity}
            )
    
    def _classify_severity(self, finding: str) -> str:
        """Classify finding severity based on keywords"""
        
        finding_lower = finding.lower()
        
        critical_keywords = ["critical", "remote code execution", "rce", "sql injection", "authentication bypass"]
        high_keywords = ["high", "vulnerability", "exploit", "exposed", "sensitive"]
        medium_keywords = ["medium", "misconfiguration", "weak", "outdated"]
        low_keywords = ["low", "information disclosure", "warning"]
        
        if any(kw in finding_lower for kw in critical_keywords):
            return "Critical"
        elif any(kw in finding_lower for kw in high_keywords):
            return "High"
        elif any(kw in finding_lower for kw in medium_keywords):
            return "Medium"
        elif any(kw in finding_lower for kw in low_keywords):
            return "Low"
        else:
            return "Info"
    
    async def _share_knowledge(self, response: str):
        """Share knowledge with other agents"""
        
        # Add to shared messages
        self.shared_knowledge["messages"].append({
            "agent_id": self.agent_id,
            "agent_number": self.agent_number,
            "content": response[:200],  # Truncate for efficiency
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent messages (last 50)
        if len(self.shared_knowledge["messages"]) > 50:
            self.shared_knowledge["messages"] = self.shared_knowledge["messages"][-50:]
    
    async def _apply_delay(self):
        """Apply delay for rate limiting and stealth"""
        
        from server.config import settings
        
        if self.stealth_mode:
            # Randomize delay more in stealth mode
            delay = random.uniform(
                settings.DEFAULT_DELAY_MIN * 2,
                settings.DEFAULT_DELAY_MAX * 3
            )
        else:
            delay = random.uniform(
                settings.DEFAULT_DELAY_MIN,
                settings.DEFAULT_DELAY_MAX
            )
        
        await asyncio.sleep(delay)
    
    async def get_status(self) -> Dict:
        """Get current agent status"""
        cpu_usage = self._last_cpu_usage
        memory_usage = self._last_memory_usage
        
        if PSUTIL_AVAILABLE and psutil:
            try:
                new_cpu = psutil.cpu_percent(interval=None)
                if new_cpu is not None:
                    cpu_usage = new_cpu
                    self._last_cpu_usage = cpu_usage
                
                memory = psutil.virtual_memory()
                memory_usage = int(memory.used / (1024 * 1024))
                self._last_memory_usage = memory_usage
            except Exception:
                pass
        
        elapsed_time = 0
        if self.start_time:
            elapsed_time = time.time() - self.start_time
        
        progress = min(100, int((len(self.execution_history) / max(1, 50)) * 100))
        if self.status == "completed":
            progress = 100
        
        result = {
            "id": self.agent_id,
            "agent_id": self.agent_id,
            "agent_number": self.agent_number,
            "status": self.status,
            "target": self.target,
            "category": self.category,
            "model": self.model_name,
            "execution_time": elapsed_time,
            "elapsed_time": elapsed_time,
            "last_command": self.last_execute,
            "last_execute": self.last_execute,
            "last_execute_time": datetime.now().isoformat() if self.execution_history else None,
            "execution_count": len(self.execution_history),
            "findings_count": len([f for f in self.shared_knowledge.get("findings", []) if f["agent_id"] == self.agent_id]),
            "stealth_mode": self.stealth_mode,
            "aggressive_mode": self.aggressive_mode,
            "progress": progress
        }
        
        if cpu_usage is not None:
            result["cpu_usage"] = cpu_usage
        if memory_usage is not None:
            result["memory_usage"] = memory_usage
        
        return result
    
    async def pause(self):
        """Pause agent execution"""
        self.paused = True
        self.status = "paused"
        
    async def resume(self):
        """Resume agent execution"""
        self.paused = False
        self.status = "running"
    
    async def stop(self):
        """Stop agent execution"""
        self.stopped = True
        self.status = "stopped"
    
    def _save_instruction_to_history(self, response: str, commands: Dict[str, str]):
        """Save only the extracted commands to instruction history - not full response"""
        timestamp = datetime.now().isoformat()
        
        for key, cmd in commands.items():
            instruction_record = {
                "id": len(self.instruction_history) + 1,
                "command": cmd,
                "agent_key": key,
                "timestamp": timestamp,
                "model_name": self.model_name,
                "target": self.target
            }
            self.instruction_history.append(instruction_record)
        
        if len(self.instruction_history) > 100:
            self.instruction_history = self.instruction_history[-100:]
    
    async def _save_single_finding(self, content: str, severity: str = "Info"):
        """Save a single finding from JSON response"""
        import uuid
        finding_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        finding_data = {
            "agent_id": self.agent_id,
            "agent_number": self.agent_number,
            "content": content,
            "severity": severity,
            "timestamp": timestamp,
            "target": self.target,
            "id": finding_id
        }
        
        self.shared_knowledge["findings"].append(finding_data)
        
        await self.memory.save_finding(
            self.agent_id, self.target, content,
            severity=severity, category=self.category
        )
        
        await self.logger.write_finding(self.agent_id, f"[{severity}] {content}", target=self.target)
        
        await self._broadcast_event("found", content, severity.lower())
        
        await self._broadcast_finding(finding_id, content, severity, timestamp)
    
    async def _broadcast_event(self, event_type: str, content: str, severity: str = None):
        """Broadcast real-time event to WebSocket clients"""
        try:
            from server.ws import manager
            
            await manager.broadcast({
                "type": "broadcast_event",
                "event_type": event_type,
                "content": content,
                "agent_id": self.agent_id,
                "model_name": self.model_name,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "target": self.target
            })
        except Exception:
            pass
    
    async def _broadcast_finding(self, finding_id: str, content: str, severity: str, timestamp: str):
        """Broadcast finding update to WebSocket clients for real-time display"""
        try:
            from server.ws import manager
            
            await manager.broadcast_finding({
                "id": finding_id,
                "title": content[:100] + ("..." if len(content) > 100 else ""),
                "description": content,
                "severity": severity.lower(),
                "agent_id": self.agent_id,
                "timestamp": timestamp,
                "cve": None,
                "cvss": None
            })
        except Exception:
            pass
    
    async def _broadcast_model_instruction(self, response: str):
        """Broadcast model instruction to WebSocket clients - only commands"""
        try:
            from server.ws import manager
            
            commands = self._extract_commands(response)
            if not commands:
                return
            
            timestamp = datetime.now().isoformat()
            
            for key, cmd in commands.items():
                await manager.broadcast({
                    "type": "broadcast_event",
                    "event_type": "command",
                    "content": cmd,
                    "agent_id": self.agent_id,
                    "model_name": self.model_name,
                    "timestamp": timestamp,
                    "target": self.target
                })
        except Exception:
            pass
    
    def get_instruction_history(self) -> List[Dict]:
        """Get the instruction history for this agent - only commands, no full response"""
        return [
            {
                "id": item.get("id"),
                "command": item.get("command"),
                "timestamp": item.get("timestamp"),
                "target": item.get("target"),
                "model_name": item.get("model_name")
            }
            for item in self.instruction_history
            if item.get("command")
        ]
