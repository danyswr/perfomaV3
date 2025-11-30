"""Per-agent queue distributor for task management - each agent has independent queue"""
from typing import Dict, List, Any, Optional
import json
import asyncio

class QueueDistributor:
    """Distributes model predictions to agent-specific queues - no waiting between agents"""
    
    def __init__(self):
        self.agent_queues: Dict[str, List[Dict]] = {}
        self.agent_locks: Dict[str, asyncio.Lock] = {}
        self.processed_commands: Dict[str, set] = {}
    
    def _get_lock(self, agent_id: str) -> asyncio.Lock:
        """Get or create lock for agent"""
        if agent_id not in self.agent_locks:
            self.agent_locks[agent_id] = asyncio.Lock()
        return self.agent_locks[agent_id]
    
    def parse_model_response(self, response: str) -> Dict[str, Any]:
        """Parse full model JSON response into structured batches"""
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
            return data
        except json.JSONDecodeError:
            return {}
    
    def distribute_to_agents(self, model_response: str, agent_map: Dict[str, int]):
        """Distribute commands to agent-specific queues based on agent number"""
        data = self.parse_model_response(model_response)
        
        if not data or data.get("status") == "END":
            return
        
        for agent_id, agent_number in agent_map.items():
            agent_key = str(agent_number)
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = []
            if agent_id not in self.processed_commands:
                self.processed_commands[agent_id] = set()
            
            for batch_name in ["batch_1", "batch_2", "batch_3"]:
                batch = data.get(batch_name, {})
                if isinstance(batch, dict) and agent_key in batch:
                    cmd = batch[agent_key]
                    if isinstance(cmd, str) and cmd.startswith("RUN "):
                        cmd_hash = hash(cmd)
                        if cmd_hash not in self.processed_commands[agent_id]:
                            self.agent_queues[agent_id].append({
                                "batch": batch_name,
                                "key": agent_key,
                                "command": cmd,
                                "status": "pending"
                            })
                            self.processed_commands[agent_id].add(cmd_hash)
    
    async def get_next_command(self, agent_id: str) -> Optional[Dict]:
        """Get next pending command for agent - async safe"""
        lock = self._get_lock(agent_id)
        async with lock:
            if agent_id in self.agent_queues:
                for cmd in self.agent_queues[agent_id]:
                    if cmd.get("status") == "pending":
                        cmd["status"] = "executing"
                        return cmd
            return None
    
    async def complete_command(self, agent_id: str, command: str, result: str = None):
        """Mark command as completed"""
        lock = self._get_lock(agent_id)
        async with lock:
            if agent_id in self.agent_queues:
                for cmd in self.agent_queues[agent_id]:
                    if cmd.get("command") == command:
                        cmd["status"] = "completed"
                        cmd["result"] = result
                        break
    
    def get_agent_queue(self, agent_id: str) -> List[Dict]:
        """Get all commands in agent queue"""
        return self.agent_queues.get(agent_id, [])
    
    def get_pending_count(self, agent_id: str) -> int:
        """Get count of pending commands for agent"""
        if agent_id in self.agent_queues:
            return sum(1 for cmd in self.agent_queues[agent_id] if cmd.get("status") == "pending")
        return 0
    
    def pop_agent_instruction(self, agent_id: str) -> Dict:
        """Pop next instruction for agent (sync version)"""
        if agent_id in self.agent_queues and self.agent_queues[agent_id]:
            for i, cmd in enumerate(self.agent_queues[agent_id]):
                if cmd.get("status") == "pending":
                    self.agent_queues[agent_id][i]["status"] = "executing"
                    return cmd
        return {}
    
    def add_instruction(self, agent_id: str, command: str):
        """Add instruction to agent queue"""
        if agent_id not in self.agent_queues:
            self.agent_queues[agent_id] = []
        if agent_id not in self.processed_commands:
            self.processed_commands[agent_id] = set()
            
        cmd_hash = hash(command)
        if cmd_hash not in self.processed_commands[agent_id]:
            self.agent_queues[agent_id].append({
                "key": "1",
                "command": command,
                "status": "pending"
            })
            self.processed_commands[agent_id].add(cmd_hash)
    
    def clear_agent_queue(self, agent_id: str):
        """Clear queue for agent"""
        if agent_id in self.agent_queues:
            self.agent_queues[agent_id] = []
        if agent_id in self.processed_commands:
            self.processed_commands[agent_id] = set()
    
    async def get_agent_commands(self, agent_id: str, limit: int = 5) -> List[str]:
        """Get pending commands for agent - for new agents joining mid-execution"""
        lock = self._get_lock(agent_id)
        async with lock:
            commands = []
            if agent_id in self.agent_queues:
                for cmd in self.agent_queues[agent_id]:
                    if cmd.get("status") == "pending" and len(commands) < limit:
                        cmd["status"] = "executing"
                        commands.append(cmd.get("command", ""))
            return commands
    
    def add_shared_instruction(self, command: str, agent_ids: List[str]):
        """Add instruction to multiple agent queues (for distributing to new agents)"""
        for agent_id in agent_ids:
            self.add_instruction(agent_id, command)


_queue_distributor_instance: Optional['QueueDistributor'] = None
_queue_lock = asyncio.Lock()

def get_queue_distributor() -> QueueDistributor:
    """Get or create global queue distributor instance"""
    global _queue_distributor_instance
    if _queue_distributor_instance is None:
        _queue_distributor_instance = QueueDistributor()
    return _queue_distributor_instance
