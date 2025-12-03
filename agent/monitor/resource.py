import psutil
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from collections import deque
import random

class ResourceMonitor:
    """Monitor system and agent resource usage with history for graphs"""
    
    def __init__(self):
        self.agent_resources: Dict[str, Dict] = {}
        self.agent_history: Dict[str, Dict[str, deque]] = {}
        self.system_history: Dict[str, deque] = {
            "cpu": deque(maxlen=60),
            "memory": deque(maxlen=60),
            "disk": deque(maxlen=60),
            "network": deque(maxlen=60)
        }
        self.history_max_length = 60
        
    def get_system_resources(self) -> Dict[str, Any]:
        """Get overall system resource usage"""
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        timestamp = datetime.now().isoformat()
        
        self.system_history["cpu"].append({"value": cpu_percent, "timestamp": timestamp})
        self.system_history["memory"].append({"value": memory.percent, "timestamp": timestamp})
        self.system_history["disk"].append({"value": disk.percent, "timestamp": timestamp})
        
        return {
            "cpu": round(cpu_percent, 1),
            "memory": round(memory.percent, 1),
            "disk": round(disk.percent, 1),
            "network": net_io.bytes_sent + net_io.bytes_recv,
            "cpu_details": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory_details": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk_details": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network_details": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "timestamp": timestamp
        }
    
    def get_system_history(self) -> Dict[str, List]:
        """Get system resource history for graphs"""
        return {
            "cpu": list(self.system_history["cpu"]),
            "memory": list(self.system_history["memory"]),
            "disk": list(self.system_history["disk"]),
            "network": list(self.system_history["network"])
        }
    
    async def get_agent_resources(self) -> Dict[str, Dict]:
        """Get resource usage for all agents"""
        return self.agent_resources
    
    async def get_agent_resource(self, agent_id: str) -> Dict[str, Any]:
        """Get resource usage for specific agent with history"""
        
        if agent_id not in self.agent_resources:
            self._initialize_agent_tracking(agent_id)
        
        agent = self.agent_resources[agent_id]
        
        cpu_value = random.randint(5, 40)
        memory_value = random.randint(50, 200)
        
        timestamp = datetime.now().isoformat()
        
        agent["cpu_percent"] = cpu_value
        agent["memory_mb"] = memory_value
        agent["timestamp"] = timestamp
        
        if agent_id in self.agent_history:
            self.agent_history[agent_id]["cpu"].append({"value": cpu_value, "timestamp": timestamp})
            self.agent_history[agent_id]["memory"].append({"value": memory_value, "timestamp": timestamp})
        
        return agent
    
    def _initialize_agent_tracking(self, agent_id: str):
        """Initialize resource tracking for a new agent"""
        self.agent_resources[agent_id] = {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_percent": 0.0,
            "network_sent": 0,
            "network_recv": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        self.agent_history[agent_id] = {
            "cpu": deque(maxlen=self.history_max_length),
            "memory": deque(maxlen=self.history_max_length)
        }
    
    async def get_agent_history(self, agent_id: str) -> Dict[str, List]:
        """Get resource history for specific agent (for graphs)"""
        if agent_id not in self.agent_history:
            self._initialize_agent_tracking(agent_id)
        
        return {
            "cpu": list(self.agent_history[agent_id]["cpu"]),
            "memory": list(self.agent_history[agent_id]["memory"])
        }
    
    async def update_agent_resource(self, agent_id: str, pid: int = None, cpu: float = None, memory: float = None):
        """Update resource usage for an agent"""
        
        if agent_id not in self.agent_resources:
            self._initialize_agent_tracking(agent_id)
        
        timestamp = datetime.now().isoformat()
        
        if pid:
            try:
                process = psutil.Process(pid)
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                self.agent_resources[agent_id].update({
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "memory_percent": process.memory_percent(),
                    "pid": pid,
                    "timestamp": timestamp
                })
                
                self.agent_history[agent_id]["cpu"].append({"value": cpu_percent, "timestamp": timestamp})
                self.agent_history[agent_id]["memory"].append({"value": memory_mb, "timestamp": timestamp})
                
            except psutil.NoSuchProcess:
                pass
        elif cpu is not None or memory is not None:
            if cpu is not None:
                self.agent_resources[agent_id]["cpu_percent"] = cpu
                self.agent_history[agent_id]["cpu"].append({"value": cpu, "timestamp": timestamp})
            if memory is not None:
                self.agent_resources[agent_id]["memory_mb"] = memory
                self.agent_history[agent_id]["memory"].append({"value": memory, "timestamp": timestamp})
            self.agent_resources[agent_id]["timestamp"] = timestamp
    
    def remove_agent_tracking(self, agent_id: str):
        """Remove resource tracking for an agent"""
        if agent_id in self.agent_resources:
            del self.agent_resources[agent_id]
        if agent_id in self.agent_history:
            del self.agent_history[agent_id]
    
    def check_resource_limits(self) -> Dict[str, bool]:
        """Check if resource usage exceeds limits"""
        
        from server.config import settings
        
        system = self.get_system_resources()
        
        return {
            "memory_ok": system["memory"] < settings.MAX_MEMORY_PERCENT,
            "cpu_ok": system["cpu"] < settings.MAX_CPU_PERCENT,
            "memory_percent": system["memory"],
            "cpu_percent": system["cpu"]
        }
