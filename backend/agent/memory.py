import aiosqlite
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class AgentMemory:
    """SQLite-based persistent memory for agents - enables powerful knowledge retention and collaboration"""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize database with all required tables"""
        if self._initialized:
            return
            
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA synchronous=NORMAL")
                await db.execute("PRAGMA cache_size=-8000")
                await db.execute("PRAGMA temp_store=MEMORY")
                
                await db.executescript("""
                    -- Agent registry table
                    CREATE TABLE IF NOT EXISTS agents (
                        agent_id TEXT PRIMARY KEY,
                        agent_number INTEGER,
                        target TEXT,
                        category TEXT,
                        model_name TEXT,
                        status TEXT DEFAULT 'idle',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    );
                    
                    -- Conversation history table
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        iteration INTEGER DEFAULT 0,
                        tokens_used INTEGER DEFAULT 0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                    );
                    
                    -- Shared knowledge base (no unique constraint to allow multiple agents to contribute)
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT NOT NULL,
                        knowledge_type TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    );
                    
                    -- Findings table
                    CREATE TABLE IF NOT EXISTS findings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT NOT NULL,
                        target TEXT,
                        content TEXT NOT NULL,
                        severity TEXT DEFAULT 'Info',
                        category TEXT,
                        verified BOOLEAN DEFAULT FALSE,
                        exploitable BOOLEAN DEFAULT FALSE,
                        cvss_score REAL,
                        cve_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    );
                    
                    -- Inter-agent messages
                    CREATE TABLE IF NOT EXISTS agent_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_agent TEXT NOT NULL,
                        to_agent TEXT,
                        message_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        priority INTEGER DEFAULT 5,
                        read_status BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    );
                    
                    -- Task queue for agent collaboration
                    CREATE TABLE IF NOT EXISTS task_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT,
                        task_type TEXT NOT NULL,
                        task_data TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        priority INTEGER DEFAULT 5,
                        assigned_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        result TEXT
                    );
                    
                    -- Execution history
                    CREATE TABLE IF NOT EXISTS execution_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT NOT NULL,
                        command TEXT NOT NULL,
                        result TEXT,
                        success BOOLEAN DEFAULT TRUE,
                        execution_time REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Resource usage tracking
                    CREATE TABLE IF NOT EXISTS resource_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_id TEXT,
                        cpu_percent REAL,
                        memory_mb REAL,
                        disk_io REAL,
                        network_bytes REAL,
                        throttle_active BOOLEAN DEFAULT FALSE,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Rate limit tracking for AI models
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        requests_count INTEGER DEFAULT 0,
                        tokens_used INTEGER DEFAULT 0,
                        last_request TIMESTAMP,
                        window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cooldown_until TIMESTAMP,
                        UNIQUE(model_name)
                    );
                    
                    -- Create indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_conv_agent ON conversation_history(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversation_history(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
                    CREATE INDEX IF NOT EXISTS idx_findings_target ON findings(target);
                    CREATE INDEX IF NOT EXISTS idx_messages_to ON agent_messages(to_agent);
                    CREATE INDEX IF NOT EXISTS idx_messages_unread ON agent_messages(to_agent, read_status);
                    CREATE INDEX IF NOT EXISTS idx_tasks_status ON task_queue(status);
                    CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_base(knowledge_type);
                """)
                await db.commit()
                self._initialized = True
    
    async def register_agent(self, agent_id: str, agent_number: int, target: str, 
                            category: str, model_name: str, metadata: Optional[Dict] = None) -> bool:
        """Register a new agent in the memory system"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT OR REPLACE INTO agents 
                    (agent_id, agent_number, target, category, model_name, status, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'active', ?, CURRENT_TIMESTAMP)
                """, (agent_id, agent_number, target, category, model_name, 
                      json.dumps(metadata or {})))
                await db.commit()
                return True
            except Exception as e:
                print(f"Error registering agent: {e}")
                return False
    
    async def update_agent_status(self, agent_id: str, status: str):
        """Update agent status"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE agents SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE agent_id = ?
            """, (status, agent_id))
            await db.commit()
    
    async def save_conversation(self, agent_id: str, role: str, content: str, 
                                iteration: int = 0, tokens: int = 0):
        """Save a conversation entry"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO conversation_history (agent_id, role, content, iteration, tokens_used)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, role, content, iteration, tokens))
            await db.commit()
    
    async def get_conversation_history(self, agent_id: str, limit: int = 20) -> List[Dict]:
        """Get recent conversation history for an agent"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT role, content, iteration, timestamp 
                FROM conversation_history 
                WHERE agent_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (agent_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(list(rows))]
    
    async def add_knowledge(self, agent_id: str, knowledge_type: str, key: str, 
                           value: Any, confidence: float = 1.0, source: Optional[str] = None):
        """Add knowledge to the shared knowledge base (allows multiple agent contributions)"""
        await self.initialize()
        
        value_json = json.dumps(value) if not isinstance(value, str) else value
        
        async with aiosqlite.connect(self.db_path) as db:
            existing = await db.execute("""
                SELECT id FROM knowledge_base 
                WHERE knowledge_type = ? AND key = ? AND agent_id = ?
            """, (knowledge_type, key, agent_id))
            row = await existing.fetchone()
            
            if row:
                await db.execute("""
                    UPDATE knowledge_base 
                    SET value = ?, confidence = ?, source = ?, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (value_json, confidence, source, row[0]))
            else:
                await db.execute("""
                    INSERT INTO knowledge_base 
                    (agent_id, knowledge_type, key, value, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent_id, knowledge_type, key, value_json, confidence, source))
            await db.commit()
    
    async def get_knowledge(self, knowledge_type: Optional[str] = None, key: Optional[str] = None) -> List[Dict]:
        """Retrieve knowledge from the knowledge base"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if knowledge_type and key:
                query = "SELECT * FROM knowledge_base WHERE knowledge_type = ? AND key = ?"
                params = (knowledge_type, key)
            elif knowledge_type:
                query = "SELECT * FROM knowledge_base WHERE knowledge_type = ?"
                params = (knowledge_type,)
            else:
                query = "SELECT * FROM knowledge_base ORDER BY created_at DESC LIMIT 100"
                params = ()
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    try:
                        d['value'] = json.loads(d['value'])
                    except:
                        pass
                    results.append(d)
                return results
    
    async def save_finding(self, agent_id: str, target: str, content: str, 
                          severity: str = "Info", category: str = None,
                          metadata: Dict = None) -> int:
        """Save a security finding"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO findings 
                (agent_id, target, content, severity, category, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_id, target, content, severity, category, 
                  json.dumps(metadata or {})))
            await db.commit()
            return cursor.lastrowid
    
    async def get_findings(self, target: str = None, severity: str = None, 
                          limit: int = 100) -> List[Dict]:
        """Get findings with optional filters"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM findings WHERE 1=1"
            params = []
            
            if target:
                query += " AND target = ?"
                params.append(target)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_findings_summary(self, target: str = None) -> Dict:
        """Get summary of findings by severity, optionally filtered by target"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            if target:
                async with db.execute("""
                    SELECT severity, COUNT(*) as count 
                    FROM findings 
                    WHERE target = ?
                    GROUP BY severity
                """, (target,)) as cursor:
                    rows = await cursor.fetchall()
                    return {row[0]: row[1] for row in rows}
            else:
                async with db.execute("""
                    SELECT severity, COUNT(*) as count 
                    FROM findings 
                    GROUP BY severity
                """) as cursor:
                    rows = await cursor.fetchall()
                    return {row[0]: row[1] for row in rows}
    
    async def get_findings_for_target(self, target: str, limit: int = 50) -> List[Dict]:
        """Get all findings specifically for a target - used by agents to see only relevant data"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT id, agent_id, target, content, severity, category, 
                       verified, exploitable, cvss_score, cve_id, created_at, metadata
                FROM findings 
                WHERE target = ?
                ORDER BY 
                    CASE severity 
                        WHEN 'Critical' THEN 1 
                        WHEN 'High' THEN 2 
                        WHEN 'Medium' THEN 3 
                        WHEN 'Low' THEN 4 
                        ELSE 5 
                    END,
                    created_at DESC
                LIMIT ?
            """, (target, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_target_context(self, target: str) -> Dict:
        """Get comprehensive context about a target for agent decision making"""
        await self.initialize()
        
        findings = await self.get_findings_for_target(target, limit=20)
        summary = await self.get_findings_summary(target)
        
        knowledge = await self.get_knowledge(knowledge_type="discovery")
        target_knowledge = [k for k in knowledge if k.get("key", "").startswith(target) or target in str(k.get("value", ""))]
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT command, result, success, execution_time, timestamp
                FROM execution_history
                WHERE command LIKE ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (f"%{target}%",)) as cursor:
                exec_history = [dict(row) for row in await cursor.fetchall()]
        
        return {
            "target": target,
            "findings": findings,
            "severity_summary": summary,
            "knowledge": target_knowledge[:10],
            "recent_executions": exec_history,
            "total_findings": len(findings)
        }
    
    async def send_agent_message(self, from_agent: str, to_agent: str, 
                                 message_type: str, content: str, 
                                 priority: int = 5) -> int:
        """Send a message to another agent"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO agent_messages 
                (from_agent, to_agent, message_type, content, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (from_agent, to_agent, message_type, content, priority))
            await db.commit()
            return cursor.lastrowid
    
    async def broadcast_message(self, from_agent: str, message_type: str, 
                               content: str, priority: int = 5) -> int:
        """Broadcast a message to all agents (to_agent = NULL)"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO agent_messages 
                (from_agent, to_agent, message_type, content, priority)
                VALUES (?, NULL, ?, ?, ?)
            """, (from_agent, message_type, content, priority))
            await db.commit()
            return cursor.lastrowid
    
    async def get_messages(self, agent_id: str, unread_only: bool = False, 
                          limit: int = 50) -> List[Dict]:
        """Get messages for an agent"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT * FROM agent_messages 
                WHERE (to_agent = ? OR to_agent IS NULL) AND from_agent != ?
            """
            params = [agent_id, agent_id]
            
            if unread_only:
                query += " AND read_status = FALSE"
            
            query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def mark_messages_read(self, agent_id: str, message_ids: List[int] = None):
        """Mark messages as read"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            if message_ids:
                placeholders = ','.join(['?' for _ in message_ids])
                await db.execute(f"""
                    UPDATE agent_messages 
                    SET read_status = TRUE 
                    WHERE id IN ({placeholders})
                """, message_ids)
            else:
                await db.execute("""
                    UPDATE agent_messages 
                    SET read_status = TRUE 
                    WHERE (to_agent = ? OR to_agent IS NULL)
                """, (agent_id,))
            await db.commit()
    
    async def add_task(self, task_type: str, task_data: Dict, 
                      priority: int = 5) -> int:
        """Add a task to the queue"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO task_queue (task_type, task_data, priority)
                VALUES (?, ?, ?)
            """, (task_type, json.dumps(task_data), priority))
            await db.commit()
            return cursor.lastrowid
    
    async def claim_task(self, agent_id: str, task_types: List[str] = None) -> Optional[Dict]:
        """Claim the next available task"""
        await self.initialize()
        
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                query = """
                    SELECT * FROM task_queue 
                    WHERE status = 'pending' AND agent_id IS NULL
                """
                params = []
                
                if task_types:
                    placeholders = ','.join(['?' for _ in task_types])
                    query += f" AND task_type IN ({placeholders})"
                    params.extend(task_types)
                
                query += " ORDER BY priority DESC, created_at ASC LIMIT 1"
                
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        task = dict(row)
                        task['task_data'] = json.loads(task['task_data'])
                        
                        await db.execute("""
                            UPDATE task_queue 
                            SET agent_id = ?, status = 'in_progress', 
                                assigned_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (agent_id, task['id']))
                        await db.commit()
                        
                        return task
                
                return None
    
    async def complete_task(self, task_id: int, result: Any = None, success: bool = True):
        """Mark a task as complete"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            status = 'completed' if success else 'failed'
            await db.execute("""
                UPDATE task_queue 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, result = ?
                WHERE id = ?
            """, (status, json.dumps(result) if result else None, task_id))
            await db.commit()
    
    async def save_execution(self, agent_id: str, command: str, result: str,
                            success: bool = True, execution_time: float = 0):
        """Save command execution history"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO execution_history 
                (agent_id, command, result, success, execution_time)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, command, result[:5000] if result else None, 
                  success, execution_time))
            await db.commit()
    
    async def record_resource_usage(self, agent_id: str, cpu: float, memory: float,
                                    disk_io: float = 0, network: float = 0,
                                    throttle: bool = False):
        """Record resource usage"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO resource_usage 
                (agent_id, cpu_percent, memory_mb, disk_io, network_bytes, throttle_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_id, cpu, memory, disk_io, network, throttle))
            await db.commit()
    
    async def update_rate_limit(self, model_name: str, tokens_used: int = 0):
        """Update rate limit tracking for a model"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO rate_limits (model_name, requests_count, tokens_used, last_request)
                VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(model_name) DO UPDATE SET
                    requests_count = requests_count + 1,
                    tokens_used = tokens_used + ?,
                    last_request = CURRENT_TIMESTAMP
            """, (model_name, tokens_used, tokens_used))
            await db.commit()
    
    async def get_rate_limit_status(self, model_name: str) -> Dict:
        """Get rate limit status for a model"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM rate_limits WHERE model_name = ?
            """, (model_name,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return {
                    "model_name": model_name,
                    "requests_count": 0,
                    "tokens_used": 0,
                    "last_request": None
                }
    
    async def set_rate_limit_cooldown(self, model_name: str, cooldown_seconds: int):
        """Set a cooldown period for a model"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE rate_limits 
                SET cooldown_until = datetime('now', '+' || ? || ' seconds')
                WHERE model_name = ?
            """, (cooldown_seconds, model_name))
            await db.commit()
    
    async def check_rate_limit_cooldown(self, model_name: str) -> bool:
        """Check if model is in cooldown"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT cooldown_until FROM rate_limits 
                WHERE model_name = ? AND cooldown_until > CURRENT_TIMESTAMP
            """, (model_name,)) as cursor:
                row = await cursor.fetchone()
                return row is not None
    
    async def get_agent_stats(self, agent_id: str) -> Dict:
        """Get comprehensive stats for an agent"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            async with db.execute("""
                SELECT COUNT(*) FROM conversation_history WHERE agent_id = ?
            """, (agent_id,)) as cursor:
                row = await cursor.fetchone()
                stats['total_conversations'] = row[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM execution_history WHERE agent_id = ?
            """, (agent_id,)) as cursor:
                row = await cursor.fetchone()
                stats['total_executions'] = row[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM findings WHERE agent_id = ?
            """, (agent_id,)) as cursor:
                row = await cursor.fetchone()
                stats['total_findings'] = row[0]
            
            async with db.execute("""
                SELECT COUNT(*) FROM agent_messages 
                WHERE from_agent = ?
            """, (agent_id,)) as cursor:
                row = await cursor.fetchone()
                stats['messages_sent'] = row[0]
            
            return stats
    
    async def cleanup_old_data(self, days: int = 7):
        """Clean up old data to prevent database bloat"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM conversation_history 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            await db.execute("""
                DELETE FROM agent_messages 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            await db.execute("""
                DELETE FROM resource_usage 
                WHERE timestamp < datetime('now', '-1 days')
            """)
            
            await db.execute("""
                DELETE FROM task_queue 
                WHERE status IN ('completed', 'failed') 
                AND completed_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            await db.commit()


    async def save_session(self, session_id: str, target: str, config: Dict, agents_state: List[Dict]) -> bool:
        """Save the current session state for resume capability"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    config TEXT NOT NULL,
                    agents_state TEXT NOT NULL,
                    status TEXT DEFAULT 'paused',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                INSERT OR REPLACE INTO sessions (id, target, config, agents_state, status, updated_at)
                VALUES (?, ?, ?, ?, 'paused', CURRENT_TIMESTAMP)
            """, (session_id, target, json.dumps(config), json.dumps(agents_state)))
            await db.commit()
            return True
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve a saved session"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    session = dict(row)
                    session['config'] = json.loads(session['config'])
                    session['agents_state'] = json.loads(session['agents_state'])
                    return session
                return None
    
    async def list_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent sessions available for resume"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    config TEXT NOT NULL,
                    agents_state TEXT NOT NULL,
                    status TEXT DEFAULT 'paused',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            
            async with db.execute("""
                SELECT id, target, status, created_at, updated_at 
                FROM sessions 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a saved session"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()
            return True
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status (running, paused, completed)"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (status, session_id))
            await db.commit()
            return True


class AgentMemoryManager:
    """Singleton manager for agent memory"""
    
    _instance: Optional['AgentMemoryManager'] = None
    _memory: Optional[AgentMemory] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._memory = AgentMemory()
        return cls._instance
    
    @property
    def memory(self) -> AgentMemory:
        if self._memory is None:
            self._memory = AgentMemory()
        return self._memory
    
    async def initialize(self):
        await self._memory.initialize()


def get_memory() -> AgentMemory:
    """Get the shared agent memory instance"""
    return AgentMemoryManager().memory
