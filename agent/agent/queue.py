from typing import Dict, List, Any
import asyncio

class QueueManager:
    """Manages command queue for agents"""
    
    def __init__(self):
        self.queue: List[Dict[str, str]] = []
        self.lock = asyncio.Lock()
        
    async def add_to_queue(self, commands: Dict[str, str]):
        """Add commands to queue"""
        async with self.lock:
            self.queue.append(commands)
    
    async def list_queue(self) -> List[Dict]:
        """List all items in queue"""
        async with self.lock:
            return [
                {"index": i + 1, "commands": cmd}
                for i, cmd in enumerate(self.queue)
            ]
    
    async def remove_from_queue(self, index: int) -> Dict:
        """Remove item from queue by index"""
        async with self.lock:
            if 0 <= index < len(self.queue):
                return self.queue.pop(index)
            raise IndexError("Queue index out of range")
    
    async def edit_queue(self, index: int, commands: Dict[str, str]):
        """Edit item in queue"""
        async with self.lock:
            if 0 <= index < len(self.queue):
                self.queue[index] = commands
            else:
                raise IndexError("Queue index out of range")
    
    async def get_next(self) -> Dict[str, str]:
        """Get next command from queue"""
        async with self.lock:
            if self.queue:
                return self.queue.pop(0)
            return {}
    
    async def clear_queue(self):
        """Clear entire queue"""
        async with self.lock:
            self.queue.clear()
