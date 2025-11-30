import asyncio
import psutil
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=2)

class ThrottleLevel(Enum):
    """Throttle intensity levels"""
    NONE = 0
    LIGHT = 1
    MODERATE = 2
    HEAVY = 3
    PAUSE = 4

@dataclass
class ResourceThresholds:
    """Resource thresholds for throttling"""
    cpu_light: float = 60.0
    cpu_moderate: float = 75.0
    cpu_heavy: float = 85.0
    cpu_pause: float = 95.0
    
    memory_light: float = 60.0
    memory_moderate: float = 75.0
    memory_heavy: float = 85.0
    memory_pause: float = 92.0
    
    disk_io_threshold: float = 80.0
    network_threshold: float = 90.0

@dataclass
class ThrottleState:
    """Current throttle state for an agent"""
    level: ThrottleLevel = ThrottleLevel.NONE
    base_delay: float = 1.0
    current_delay: float = 1.0
    pause_until: Optional[datetime] = None
    consecutive_high_usage: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    reason: str = ""

def _blocking_get_cpu() -> float:
    """Get CPU percent in a blocking way (for thread pool)"""
    try:
        return psutil.cpu_percent(interval=0.1)
    except:
        return 0.0

def _blocking_get_memory() -> Dict:
    """Get memory info in a blocking way (for thread pool)"""
    try:
        mem = psutil.virtual_memory()
        return {"percent": mem.percent, "available": mem.available}
    except:
        return {"percent": 0, "available": 0}

class IntelligentThrottler:
    """
    Intelligent Throttling System for Agents
    
    Monitors CPU, RAM, disk I/O, and network usage in real-time.
    Automatically adjusts agent execution speed based on resource availability.
    """
    
    def __init__(self, thresholds: ResourceThresholds = None):
        self.thresholds = thresholds or ResourceThresholds()
        self.agent_states: Dict[str, ThrottleState] = {}
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_system_check: Dict[str, float] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
        self._disk_io_baseline = self._get_disk_io()
        self._network_baseline = self._get_network_io()
        self._cached_resources: Dict[str, float] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 1.0
        self._max_agent_states = 15
        self._cleanup_interval = 30
        self._last_cleanup: datetime = datetime.now()
    
    def _get_disk_io(self) -> float:
        """Get current disk I/O"""
        try:
            counters = psutil.disk_io_counters()
            return counters.read_bytes + counters.write_bytes if counters else 0
        except:
            return 0
    
    def _get_network_io(self) -> float:
        """Get current network I/O"""
        try:
            net = psutil.net_io_counters()
            return net.bytes_sent + net.bytes_recv
        except:
            return 0
    
    async def get_system_resources_async(self) -> Dict[str, float]:
        """Get current system resource usage without blocking the event loop"""
        now = datetime.now()
        if self._cache_time and (now - self._cache_time).total_seconds() < self._cache_ttl:
            return self._cached_resources
        
        try:
            loop = asyncio.get_event_loop()
            cpu_task = loop.run_in_executor(_executor, _blocking_get_cpu)
            mem_task = loop.run_in_executor(_executor, _blocking_get_memory)
            
            cpu, memory = await asyncio.gather(cpu_task, mem_task)
            
            current_disk = self._get_disk_io()
            disk_io_rate = (current_disk - self._disk_io_baseline) / 1024 / 1024
            self._disk_io_baseline = current_disk
            
            current_network = self._get_network_io()
            network_rate = (current_network - self._network_baseline) / 1024 / 1024
            self._network_baseline = current_network
            
            self._cached_resources = {
                "cpu_percent": cpu,
                "memory_percent": memory["percent"],
                "memory_available_mb": memory["available"] / 1024 / 1024,
                "disk_io_mbps": max(0, disk_io_rate),
                "network_mbps": max(0, network_rate),
                "timestamp": now.isoformat()
            }
            self._cache_time = now
            
            return self._cached_resources
        except Exception as e:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_available_mb": 0,
                "disk_io_mbps": 0,
                "network_mbps": 0,
                "error": str(e)
            }
    
    def get_system_resources(self) -> Dict[str, float]:
        """Get cached system resources (non-blocking, may be slightly stale)"""
        if self._cached_resources:
            return self._cached_resources
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_mb": 0,
            "disk_io_mbps": 0,
            "network_mbps": 0
        }
    
    def calculate_throttle_level(self, resources: Dict[str, float]) -> tuple[ThrottleLevel, str]:
        """Calculate the appropriate throttle level based on resources"""
        cpu = resources.get("cpu_percent", 0)
        memory = resources.get("memory_percent", 0)
        
        reasons = []
        max_level = ThrottleLevel.NONE
        
        if cpu >= self.thresholds.cpu_pause:
            max_level = ThrottleLevel.PAUSE
            reasons.append(f"CPU critical ({cpu:.1f}%)")
        elif cpu >= self.thresholds.cpu_heavy:
            if max_level.value < ThrottleLevel.HEAVY.value:
                max_level = ThrottleLevel.HEAVY
            reasons.append(f"CPU high ({cpu:.1f}%)")
        elif cpu >= self.thresholds.cpu_moderate:
            if max_level.value < ThrottleLevel.MODERATE.value:
                max_level = ThrottleLevel.MODERATE
            reasons.append(f"CPU elevated ({cpu:.1f}%)")
        elif cpu >= self.thresholds.cpu_light:
            if max_level.value < ThrottleLevel.LIGHT.value:
                max_level = ThrottleLevel.LIGHT
            reasons.append(f"CPU moderate ({cpu:.1f}%)")
        
        if memory >= self.thresholds.memory_pause:
            max_level = ThrottleLevel.PAUSE
            reasons.append(f"Memory critical ({memory:.1f}%)")
        elif memory >= self.thresholds.memory_heavy:
            if max_level.value < ThrottleLevel.HEAVY.value:
                max_level = ThrottleLevel.HEAVY
            reasons.append(f"Memory high ({memory:.1f}%)")
        elif memory >= self.thresholds.memory_moderate:
            if max_level.value < ThrottleLevel.MODERATE.value:
                max_level = ThrottleLevel.MODERATE
            reasons.append(f"Memory elevated ({memory:.1f}%)")
        elif memory >= self.thresholds.memory_light:
            if max_level.value < ThrottleLevel.LIGHT.value:
                max_level = ThrottleLevel.LIGHT
            reasons.append(f"Memory moderate ({memory:.1f}%)")
        
        reason = "; ".join(reasons) if reasons else "Resources normal"
        return max_level, reason
    
    def get_delay_for_level(self, level: ThrottleLevel, base_delay: float = 1.0) -> float:
        """Get the delay multiplier for a throttle level"""
        multipliers = {
            ThrottleLevel.NONE: 1.0,
            ThrottleLevel.LIGHT: 1.5,
            ThrottleLevel.MODERATE: 2.5,
            ThrottleLevel.HEAVY: 5.0,
            ThrottleLevel.PAUSE: 15.0
        }
        
        jitter = random.uniform(0.8, 1.2)
        return base_delay * multipliers[level] * jitter
    
    def register_agent(self, agent_id: str, base_delay: float = 1.0):
        """Register an agent for throttling"""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = ThrottleState(
                base_delay=base_delay,
                current_delay=base_delay
            )
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from throttling"""
        if agent_id in self.agent_states:
            del self.agent_states[agent_id]
        if agent_id in self._callbacks:
            del self._callbacks[agent_id]
    
    def _cleanup_stale_agents(self):
        """Remove stale agent states to prevent memory growth"""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        stale_threshold = timedelta(minutes=5)
        stale_agents = []
        
        for agent_id, state in self.agent_states.items():
            if (now - state.last_check) > stale_threshold:
                stale_agents.append(agent_id)
        
        for agent_id in stale_agents:
            self.unregister_agent(agent_id)
        
        if len(self.agent_states) > self._max_agent_states:
            sorted_agents = sorted(
                self.agent_states.items(),
                key=lambda x: x[1].last_check
            )
            for agent_id, _ in sorted_agents[:len(sorted_agents) - self._max_agent_states]:
                self.unregister_agent(agent_id)
    
    async def check_and_throttle(self, agent_id: str) -> Dict[str, Any]:
        """
        Check resources and apply throttling for an agent.
        Returns the current throttle state and recommended delay.
        """
        self._cleanup_stale_agents()
        
        async with self._lock:
            if agent_id not in self.agent_states:
                self.register_agent(agent_id)
        
        state = self.agent_states[agent_id]
        
        if state.pause_until and datetime.now() < state.pause_until:
            wait_seconds = (state.pause_until - datetime.now()).total_seconds()
            return {
                "throttle_level": ThrottleLevel.PAUSE.name,
                "should_pause": True,
                "pause_remaining": wait_seconds,
                "delay": 0,
                "reason": f"Paused until resources stabilize ({wait_seconds:.1f}s remaining)"
            }
        
        resources = await self.get_system_resources_async()
        level, reason = self.calculate_throttle_level(resources)
        
        if level == ThrottleLevel.PAUSE:
            state.consecutive_high_usage += 1
            if state.consecutive_high_usage >= 3:
                pause_duration = min(60, 10 * state.consecutive_high_usage)
                state.pause_until = datetime.now() + timedelta(seconds=pause_duration)
                state.reason = f"Auto-paused for {pause_duration}s: {reason}"
                
                if agent_id in self._callbacks:
                    try:
                        await self._callbacks[agent_id]("pause", state)
                    except:
                        pass
                
                return {
                    "throttle_level": level.name,
                    "should_pause": True,
                    "pause_remaining": pause_duration,
                    "delay": 0,
                    "reason": state.reason,
                    "resources": resources
                }
        else:
            if level.value < ThrottleLevel.HEAVY.value:
                state.consecutive_high_usage = max(0, state.consecutive_high_usage - 1)
            state.pause_until = None
        
        state.level = level
        state.current_delay = self.get_delay_for_level(level, state.base_delay)
        state.last_check = datetime.now()
        state.reason = reason
        
        return {
            "throttle_level": level.name,
            "should_pause": False,
            "delay": state.current_delay,
            "reason": reason,
            "resources": resources,
            "consecutive_high": state.consecutive_high_usage
        }
    
    async def wait_for_resources(self, agent_id: str) -> float:
        """
        Wait based on current throttle level.
        Returns the actual delay applied.
        """
        check_result = await self.check_and_throttle(agent_id)
        
        if check_result.get("should_pause"):
            pause_time = check_result.get("pause_remaining", 10)
            await asyncio.sleep(pause_time)
            return pause_time
        
        delay = check_result.get("delay", 1.0)
        if delay > 0:
            await asyncio.sleep(delay)
        
        return delay
    
    def set_callback(self, agent_id: str, callback: Callable):
        """Set a callback for throttle events"""
        self._callbacks[agent_id] = callback
    
    def get_all_states(self) -> Dict[str, Dict]:
        """Get throttle states for all agents"""
        return {
            agent_id: {
                "level": state.level.name,
                "current_delay": state.current_delay,
                "reason": state.reason,
                "consecutive_high": state.consecutive_high_usage,
                "paused": state.pause_until is not None and datetime.now() < state.pause_until
            }
            for agent_id, state in self.agent_states.items()
        }
    
    async def start_monitoring(self, interval: float = 2.0):
        """Start background resource monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        
        async def monitor_loop():
            while self._monitoring:
                try:
                    resources = self.get_system_resources()
                    self._last_system_check = resources
                    
                    for agent_id in list(self.agent_states.keys()):
                        await self.check_and_throttle(agent_id)
                    
                except Exception as e:
                    print(f"Throttler monitor error: {e}")
                
                await asyncio.sleep(interval)
        
        self._monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass


class RateLimiter:
    """
    Rate limiter for AI model API calls.
    Prevents hitting rate limits by enforcing delays between requests.
    """
    
    def __init__(self):
        self._model_state: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._max_model_states = 10
        self._last_cleanup: datetime = datetime.now()
        self._cleanup_interval = 60
        
        self.default_limits = {
            "requests_per_minute": 60,
            "tokens_per_minute": 90000,
            "min_delay": 1.0,
            "max_delay": 30.0,
            "backoff_multiplier": 2.0
        }
        
        self.model_specific_limits = {
            "claude-3-5-sonnet": {"requests_per_minute": 50, "min_delay": 1.2},
            "gpt-4-turbo": {"requests_per_minute": 40, "min_delay": 1.5},
            "gpt-4o": {"requests_per_minute": 60, "min_delay": 1.0},
            "gpt-4o-mini": {"requests_per_minute": 100, "min_delay": 0.6},
            "claude-3-opus": {"requests_per_minute": 30, "min_delay": 2.0},
            "claude-3-haiku": {"requests_per_minute": 100, "min_delay": 0.6},
            "gemini-pro": {"requests_per_minute": 60, "min_delay": 1.0},
        }
    
    def _get_model_config(self, model_name: str) -> Dict:
        """Get rate limit config for a model"""
        model_key = model_name.lower().split("/")[-1] if "/" in model_name else model_name.lower()
        
        for key, config in self.model_specific_limits.items():
            if key in model_key:
                merged = {**self.default_limits, **config}
                return merged
        
        return self.default_limits.copy()
    
    def _cleanup_stale_models(self):
        """Remove stale model states to prevent memory growth"""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        stale_threshold = timedelta(minutes=10)
        stale_models = []
        
        for model_name, state in self._model_state.items():
            last_req = state.get("last_request")
            if last_req and (now - last_req) > stale_threshold:
                stale_models.append(model_name)
        
        for model_name in stale_models:
            del self._model_state[model_name]
        
        if len(self._model_state) > self._max_model_states:
            sorted_models = sorted(
                self._model_state.items(),
                key=lambda x: x[1].get("last_request") or datetime.min
            )
            for model_name, _ in sorted_models[:len(sorted_models) - self._max_model_states]:
                del self._model_state[model_name]
    
    def _get_state(self, model_name: str) -> Dict:
        """Get or create state for a model"""
        self._cleanup_stale_models()
        
        if model_name not in self._model_state:
            self._model_state[model_name] = {
                "requests_this_minute": 0,
                "tokens_this_minute": 0,
                "minute_start": datetime.now(),
                "last_request": None,
                "consecutive_errors": 0,
                "current_delay": self._get_model_config(model_name)["min_delay"],
                "in_cooldown": False,
                "cooldown_until": None
            }
        return self._model_state[model_name]
    
    async def acquire(self, model_name: str, estimated_tokens: int = 0) -> Dict:
        """
        Acquire permission to make an API call.
        Returns delay info and whether to proceed.
        """
        async with self._lock:
            config = self._get_model_config(model_name)
            state = self._get_state(model_name)
            
            if state["in_cooldown"] and state["cooldown_until"]:
                if datetime.now() < state["cooldown_until"]:
                    wait_time = (state["cooldown_until"] - datetime.now()).total_seconds()
                    return {
                        "proceed": False,
                        "wait_time": wait_time,
                        "reason": f"Rate limit cooldown ({wait_time:.1f}s remaining)"
                    }
                else:
                    state["in_cooldown"] = False
                    state["cooldown_until"] = None
                    state["consecutive_errors"] = 0
            
            now = datetime.now()
            if (now - state["minute_start"]).total_seconds() >= 60:
                state["requests_this_minute"] = 0
                state["tokens_this_minute"] = 0
                state["minute_start"] = now
                state["current_delay"] = config["min_delay"]
            
            if state["requests_this_minute"] >= config["requests_per_minute"] * 0.9:
                wait_time = 60 - (now - state["minute_start"]).total_seconds()
                state["current_delay"] = min(
                    state["current_delay"] * 1.5,
                    config["max_delay"]
                )
                if wait_time > 0:
                    return {
                        "proceed": True,
                        "wait_time": wait_time,
                        "reason": "Approaching rate limit, waiting for reset"
                    }
            
            if state["tokens_this_minute"] + estimated_tokens >= config["tokens_per_minute"] * 0.9:
                wait_time = 60 - (now - state["minute_start"]).total_seconds()
                return {
                    "proceed": True,
                    "wait_time": max(wait_time, state["current_delay"]),
                    "reason": "Approaching token limit"
                }
            
            delay = state["current_delay"]
            if state["last_request"]:
                elapsed = (now - state["last_request"]).total_seconds()
                if elapsed < delay:
                    delay = delay - elapsed
                else:
                    delay = 0
            
            jitter = random.uniform(0.1, 0.5)
            delay += jitter
            
            return {
                "proceed": True,
                "wait_time": delay,
                "reason": "Normal rate limiting"
            }
    
    async def record_request(self, model_name: str, tokens_used: int = 0, success: bool = True):
        """Record that a request was made"""
        async with self._lock:
            state = self._get_state(model_name)
            config = self._get_model_config(model_name)
            
            state["requests_this_minute"] += 1
            state["tokens_this_minute"] += tokens_used
            state["last_request"] = datetime.now()
            
            if success:
                state["consecutive_errors"] = 0
                if state["current_delay"] > config["min_delay"]:
                    state["current_delay"] = max(
                        config["min_delay"],
                        state["current_delay"] * 0.9
                    )
            else:
                state["consecutive_errors"] += 1
                state["current_delay"] = min(
                    config["max_delay"],
                    state["current_delay"] * config["backoff_multiplier"]
                )
    
    async def handle_rate_limit_error(self, model_name: str, retry_after: int = None):
        """Handle a rate limit error from the API"""
        async with self._lock:
            state = self._get_state(model_name)
            config = self._get_model_config(model_name)
            
            state["in_cooldown"] = True
            
            if retry_after:
                cooldown = retry_after
            else:
                cooldown = min(
                    config["max_delay"] * (2 ** state["consecutive_errors"]),
                    300
                )
            
            state["cooldown_until"] = datetime.now() + timedelta(seconds=cooldown)
            state["consecutive_errors"] += 1
            
            return {
                "cooldown_seconds": cooldown,
                "retry_at": state["cooldown_until"].isoformat()
            }
    
    def get_status(self, model_name: str = None) -> Dict:
        """Get rate limit status"""
        if model_name:
            state = self._get_state(model_name)
            return {
                "model": model_name,
                "requests_this_minute": state["requests_this_minute"],
                "tokens_this_minute": state["tokens_this_minute"],
                "current_delay": state["current_delay"],
                "in_cooldown": state["in_cooldown"],
                "consecutive_errors": state["consecutive_errors"]
            }
        
        return {
            model: {
                "requests": s["requests_this_minute"],
                "tokens": s["tokens_this_minute"],
                "delay": s["current_delay"],
                "cooldown": s["in_cooldown"]
            }
            for model, s in self._model_state.items()
        }


throttler = IntelligentThrottler()
rate_limiter = RateLimiter()
