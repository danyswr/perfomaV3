from agent.manager import AgentManager
from agent.worker import AgentWorker
from agent.executor import CommandExecutor
from agent.queue import QueueManager
from agent.memory import AgentMemory, AgentMemoryManager, get_memory
from agent.throttle import (
    IntelligentThrottler, RateLimiter, ThrottleLevel
)
from agent.collaboration import (
    InterAgentCommunication, KnowledgeBase, AgentCapability,
    MessageType, Priority, AgentMessage
)

_agent_manager_instance = None

def get_agent_manager() -> AgentManager:
    """Get the shared AgentManager singleton instance"""
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = AgentManager()
    return _agent_manager_instance

__all__ = [
    "AgentManager",
    "AgentWorker", 
    "CommandExecutor",
    "QueueManager",
    "get_agent_manager",
    "AgentMemory",
    "AgentMemoryManager",
    "get_memory",
    "IntelligentThrottler",
    "RateLimiter",
    "ThrottleLevel",
    "InterAgentCommunication",
    "KnowledgeBase",
    "AgentCapability",
    "MessageType",
    "Priority",
    "AgentMessage"
]
