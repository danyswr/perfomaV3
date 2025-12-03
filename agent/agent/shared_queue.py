"""Global shared instruction queue - any agent picks up next available command"""
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import json

class SharedInstructionQueue:
    """Global shared queue where agents pick up next available instruction"""
    
    def __init__(self):
        self.instructions: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()
        self.instruction_counter = 0
        self.executed_instructions: List[Dict[str, Any]] = []
        self._listeners: List[asyncio.Queue] = []
        self._max_executed_history = 25
        self._max_instructions = 50
    
    def add_listener(self) -> asyncio.Queue:
        """Add a listener for queue updates"""
        queue = asyncio.Queue()
        self._listeners.append(queue)
        return queue
    
    def remove_listener(self, queue: asyncio.Queue):
        """Remove a listener"""
        if queue in self._listeners:
            self._listeners.remove(queue)
    
    def _trim_executed_history(self):
        """Trim executed instructions to prevent memory growth"""
        if len(self.executed_instructions) > self._max_executed_history:
            excess = len(self.executed_instructions) - self._max_executed_history
            del self.executed_instructions[:excess]
    
    def _trim_instructions(self):
        """Trim pending instructions if queue is too long"""
        pending = [i for i in self.instructions if i["status"] == "pending"]
        if len(pending) > self._max_instructions:
            excess = len(pending) - self._max_instructions
            to_remove = pending[:excess]
            for item in to_remove:
                self.instructions.remove(item)
    
    def _get_queue_state_unlocked(self) -> Dict[str, Any]:
        """Get current queue state without acquiring lock (internal use only)"""
        pending = [i for i in self.instructions if i["status"] == "pending"]
        executing = [i for i in self.instructions if i["status"] == "executing"]
        return {
            "pending": pending,
            "executing": executing,
            "total_pending": len(pending),
            "total_executing": len(executing),
            "total_completed": len(self.executed_instructions),
            "recent_completed": self.executed_instructions[-8:]
        }
    
    def _notify_listeners_sync(self, queue_state: Dict[str, Any]):
        """Notify all listeners synchronously (call after releasing lock)"""
        for listener in self._listeners:
            try:
                listener.put_nowait(queue_state)
            except:
                pass
    
    async def add_instructions(self, commands: List[str]) -> int:
        """Add multiple instructions to queue, returns number added"""
        queue_state = None
        added = 0
        async with self.lock:
            for cmd in commands:
                if cmd and cmd.strip():
                    self.instruction_counter += 1
                    self.instructions.append({
                        "id": self.instruction_counter,
                        "command": cmd.strip(),
                        "status": "pending",
                        "added_at": datetime.now().isoformat(),
                        "claimed_by": None,
                        "started_at": None,
                        "completed_at": None
                    })
                    added += 1
            self._trim_instructions()
            queue_state = self._get_queue_state_unlocked()
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return added
    
    async def add_instruction(self, command: str) -> int:
        """Add single instruction to queue, returns instruction id"""
        queue_state = None
        result = -1
        async with self.lock:
            if command and command.strip():
                self.instruction_counter += 1
                self.instructions.append({
                    "id": self.instruction_counter,
                    "command": command.strip(),
                    "status": "pending",
                    "added_at": datetime.now().isoformat(),
                    "claimed_by": None,
                    "started_at": None,
                    "completed_at": None
                })
                result = self.instruction_counter
                queue_state = self._get_queue_state_unlocked()
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return result
    
    async def claim_next(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Agent claims next available instruction - first available wins"""
        queue_state = None
        claimed = None
        async with self.lock:
            for instruction in self.instructions:
                if instruction["status"] == "pending":
                    instruction["status"] = "executing"
                    instruction["claimed_by"] = agent_id
                    instruction["started_at"] = datetime.now().isoformat()
                    claimed = instruction.copy()
                    queue_state = self._get_queue_state_unlocked()
                    break
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return claimed
    
    async def complete_instruction(self, instruction_id: int, agent_id: str, result: str = "") -> bool:
        """Mark instruction as completed"""
        queue_state = None
        success = False
        async with self.lock:
            for instruction in self.instructions:
                if instruction["id"] == instruction_id and instruction["claimed_by"] == agent_id:
                    instruction["status"] = "completed"
                    instruction["completed_at"] = datetime.now().isoformat()
                    instruction["result"] = result[:500] if result else ""
                    self.executed_instructions.append(instruction.copy())
                    self.instructions.remove(instruction)
                    self._trim_executed_history()
                    success = True
                    queue_state = self._get_queue_state_unlocked()
                    break
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return success
    
    async def fail_instruction(self, instruction_id: int, agent_id: str, error: str = "") -> bool:
        """Mark instruction as failed and put back in queue"""
        queue_state = None
        success = False
        async with self.lock:
            for instruction in self.instructions:
                if instruction["id"] == instruction_id and instruction["claimed_by"] == agent_id:
                    instruction["status"] = "pending"
                    instruction["claimed_by"] = None
                    instruction["started_at"] = None
                    instruction["error"] = error
                    success = True
                    queue_state = self._get_queue_state_unlocked()
                    break
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return success
    
    async def get_queue_state(self) -> Dict[str, Any]:
        """Get current queue state for UI display"""
        async with self.lock:
            return self._get_queue_state_unlocked()
    
    async def get_pending_instructions(self) -> List[Dict[str, Any]]:
        """Get all pending instructions"""
        async with self.lock:
            return [i.copy() for i in self.instructions if i["status"] == "pending"]
    
    async def get_all_instructions(self) -> List[Dict[str, Any]]:
        """Get all instructions in queue"""
        async with self.lock:
            return [i.copy() for i in self.instructions]
    
    async def remove_instruction(self, instruction_id: int) -> bool:
        """Remove instruction by id"""
        queue_state = None
        success = False
        async with self.lock:
            for i, instruction in enumerate(self.instructions):
                if instruction["id"] == instruction_id:
                    self.instructions.pop(i)
                    success = True
                    queue_state = self._get_queue_state_unlocked()
                    break
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return success
    
    async def edit_instruction(self, instruction_id: int, new_command: str) -> bool:
        """Edit pending instruction"""
        queue_state = None
        success = False
        async with self.lock:
            for instruction in self.instructions:
                if instruction["id"] == instruction_id and instruction["status"] == "pending":
                    instruction["command"] = new_command.strip()
                    success = True
                    queue_state = self._get_queue_state_unlocked()
                    break
        if queue_state:
            self._notify_listeners_sync(queue_state)
        return success
    
    async def clear_queue(self):
        """Clear all pending instructions"""
        queue_state = None
        async with self.lock:
            self.instructions = [i for i in self.instructions if i["status"] == "executing"]
            queue_state = self._get_queue_state_unlocked()
        if queue_state:
            self._notify_listeners_sync(queue_state)
    
    async def add_batch_predictions(self, predictions: Dict[str, str]) -> int:
        """Add batch predictions from model (format: {"1": "RUN cmd1", "2": "RUN cmd2", ...})"""
        commands = []
        for key in sorted(predictions.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            cmd = predictions[key]
            if cmd and cmd.strip():
                commands.append(cmd.strip())
        return await self.add_instructions(commands)
    
    def parse_model_predictions(self, response: str) -> Dict[str, str]:
        """Parse model response to extract batch predictions"""
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
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    if key.isdigit() and isinstance(value, str):
                        result[key] = value
                return result
        except:
            pass
        return {}


_shared_queue_instance: Optional[SharedInstructionQueue] = None

def get_shared_queue() -> SharedInstructionQueue:
    """Get or create global shared queue instance"""
    global _shared_queue_instance
    if _shared_queue_instance is None:
        _shared_queue_instance = SharedInstructionQueue()
    return _shared_queue_instance
