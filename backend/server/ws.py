from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional, List
import json
import asyncio
from datetime import datetime
import hashlib
from agent import get_agent_manager
from agent.shared_queue import get_shared_queue

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.chat_mode: Dict[WebSocket, str] = {}
        self._broadcast_task: Optional[asyncio.Task] = None
        self._history_broadcast_task: Optional[asyncio.Task] = None
        self._queue_broadcast_task: Optional[asyncio.Task] = None
        self._last_history_hash: str = ""
        self._last_queue_hash: str = ""
        self._running = False
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.chat_mode[websocket] = "chat"
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        if websocket in self.chat_mode:
            del self.chat_mode[websocket]
        if not self.active_connections:
            self._stop_broadcast_tasks()
            
    def _stop_broadcast_tasks(self):
        """Cancel broadcast tasks when no clients are connected"""
        self._running = False
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
        if self._history_broadcast_task and not self._history_broadcast_task.done():
            self._history_broadcast_task.cancel()
        if self._queue_broadcast_task and not self._queue_broadcast_task.done():
            self._queue_broadcast_task.cancel()
        self._broadcast_task = None
        self._history_broadcast_task = None
        self._queue_broadcast_task = None
            
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients immediately"""
        if not self.active_connections:
            return
            
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.add(connection)
        
        for conn in dead_connections:
            self.disconnect(conn)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except:
            self.disconnect(websocket)
    
    def start_broadcast_task(self):
        """Start background broadcast tasks if not already running"""
        if self._running:
            return
        self._running = True
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_agent_updates())
        if self._history_broadcast_task is None or self._history_broadcast_task.done():
            self._history_broadcast_task = asyncio.create_task(self._broadcast_history_updates())
        if self._queue_broadcast_task is None or self._queue_broadcast_task.done():
            self._queue_broadcast_task = asyncio.create_task(self._broadcast_queue_updates())
    
    def _compute_hash(self, data: any) -> str:
        """Compute hash of data to detect changes"""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _broadcast_agent_updates(self):
        """Periodically broadcast agent status updates - 200ms for real-time feel"""
        agent_mgr = get_agent_manager()
        while self._running:
            try:
                if self.active_connections:
                    agents = await agent_mgr.get_all_agents()
                    await self.broadcast({
                        "type": "agent_update",
                        "agents": agents,
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Broadcast error: {e}")
            await asyncio.sleep(0.2)
    
    async def _broadcast_history_updates(self):
        """Periodically broadcast instruction history updates"""
        agent_mgr = get_agent_manager()
        while self._running:
            try:
                if self.active_connections:
                    history = await agent_mgr.get_all_instruction_history()
                    recent_history = history[-20:] if history else []
                    current_hash = self._compute_hash(recent_history)
                    
                    if current_hash != self._last_history_hash:
                        self._last_history_hash = current_hash
                        await self.broadcast({
                            "type": "history_update",
                            "history": recent_history,
                            "total": len(history),
                            "timestamp": datetime.now().isoformat()
                        })
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"History broadcast error: {e}")
            await asyncio.sleep(0.3)
    
    async def _broadcast_queue_updates(self):
        """Periodically broadcast shared queue state - 200ms for real-time"""
        shared_queue = get_shared_queue()
        while self._running:
            try:
                if self.active_connections:
                    queue_state = await shared_queue.get_queue_state()
                    current_hash = self._compute_hash(queue_state)
                    
                    if current_hash != self._last_queue_hash:
                        self._last_queue_hash = current_hash
                        await self.broadcast({
                            "type": "queue_update",
                            "queue": queue_state,
                            "timestamp": datetime.now().isoformat()
                        })
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue broadcast error: {e}")
            await asyncio.sleep(0.2)
    
    async def broadcast_finding(self, finding: dict):
        """Broadcast a new finding immediately to all clients"""
        if not self.active_connections:
            return
        
        await self.broadcast({
            "type": "finding_update",
            "finding": finding,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_agent_log(self, agent_id: str, log_entry: dict):
        """Broadcast real-time agent log entry to all clients"""
        if not self.active_connections:
            return
        
        await self.broadcast({
            "type": "agent_log",
            "agent_id": agent_id,
            "log": log_entry,
            "timestamp": datetime.now().isoformat()
        })

manager = ConnectionManager()

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    manager.start_broadcast_task()
    
    agent_mgr = get_agent_manager()
    shared_queue = get_shared_queue()
    
    try:
        queue_state = await shared_queue.get_queue_state()
        await manager.send_personal({
            "type": "system",
            "message": "Connected to Autonomous CyberSec AI Agent System",
            "mode": "chat",
            "queue": queue_state,
            "commands": {
                "/chat": "Switch to chat mode",
                "/queue list": "List command queue",
                "/queue add": "Add command to queue",
                "/queue rm <index>": "Remove command from queue",
                "/queue clear": "Clear all pending commands"
            }
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "command":
                await handle_command(message.get("content", ""), websocket)
            elif message.get("type") == "chat":
                await handle_chat(message.get("content", ""), websocket)
            elif message.get("type") == "get_updates":
                agents = await agent_mgr.get_all_agents()
                queue_state = await shared_queue.get_queue_state()
                await manager.send_personal({
                    "type": "agent_update",
                    "agents": agents,
                    "queue": queue_state
                }, websocket)
            elif message.get("type") == "get_queue":
                queue_state = await shared_queue.get_queue_state()
                await manager.send_personal({
                    "type": "queue_update",
                    "queue": queue_state
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_command(content: str, websocket: WebSocket):
    """Handle special commands like /chat, /queue"""
    content = content.strip()
    shared_queue = get_shared_queue()
    
    if content == "/chat":
        manager.chat_mode[websocket] = "chat"
        await manager.send_personal({
            "type": "mode_change",
            "mode": "chat",
            "message": "Switched to chat mode. You can now chat with the AI model."
        }, websocket)
        
    elif content.startswith("/queue"):
        parts = content.split(maxsplit=2)
        
        if len(parts) == 1 or parts[1] == "list":
            queue_state = await shared_queue.get_queue_state()
            instructions = await shared_queue.get_all_instructions()
            await manager.send_personal({
                "type": "queue_list",
                "queue": [{"index": i+1, "command": inst.get("command", "")} for i, inst in enumerate(instructions)],
                "state": queue_state,
                "total": len(instructions)
            }, websocket)
            
        elif parts[1] == "add" and len(parts) == 3:
            try:
                data = json.loads(parts[2])
                if isinstance(data, dict):
                    commands = [v for k, v in sorted(data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999) if isinstance(v, str)]
                    added = await shared_queue.add_instructions(commands)
                    queue_state = await shared_queue.get_queue_state()
                    await manager.send_personal({
                        "type": "queue_add",
                        "message": f"Added {added} commands to queue",
                        "added": added,
                        "queue": queue_state
                    }, websocket)
                    await manager.broadcast({
                        "type": "queue_update",
                        "queue": queue_state,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await manager.send_personal({
                        "type": "error",
                        "message": "Invalid format. Use: {\"1\": \"RUN cmd\", \"2\": \"RUN cmd2\"}"
                    }, websocket)
            except json.JSONDecodeError:
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
                
        elif parts[1] == "rm" and len(parts) == 3:
            try:
                instruction_id = int(parts[2])
                removed = await shared_queue.remove_instruction(instruction_id)
                queue_state = await shared_queue.get_queue_state()
                if removed:
                    await manager.send_personal({
                        "type": "queue_remove",
                        "message": f"Command #{instruction_id} removed from queue",
                        "queue": queue_state
                    }, websocket)
                    await manager.broadcast({
                        "type": "queue_update",
                        "queue": queue_state,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await manager.send_personal({
                        "type": "error",
                        "message": f"Command #{instruction_id} not found"
                    }, websocket)
            except ValueError:
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid instruction ID"
                }, websocket)
        
        elif parts[1] == "clear":
            await shared_queue.clear_queue()
            queue_state = await shared_queue.get_queue_state()
            await manager.send_personal({
                "type": "queue_clear",
                "message": "Queue cleared",
                "queue": queue_state
            }, websocket)
            await manager.broadcast({
                "type": "queue_update",
                "queue": queue_state,
                "timestamp": datetime.now().isoformat()
            })
                
        elif parts[1] == "edit" and len(parts) == 3:
            try:
                subparts = parts[2].split(maxsplit=1)
                instruction_id = int(subparts[0])
                new_command = subparts[1].strip()
                if new_command.startswith('"') and new_command.endswith('"'):
                    new_command = new_command[1:-1]
                edited = await shared_queue.edit_instruction(instruction_id, new_command)
                queue_state = await shared_queue.get_queue_state()
                if edited:
                    await manager.send_personal({
                        "type": "queue_edit",
                        "message": f"Command #{instruction_id} updated",
                        "queue": queue_state
                    }, websocket)
                    await manager.broadcast({
                        "type": "queue_update",
                        "queue": queue_state,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await manager.send_personal({
                        "type": "error",
                        "message": f"Command #{instruction_id} not found or already executing"
                    }, websocket)
            except (ValueError, IndexError):
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid format. Use: /queue edit <id> <new_command>"
                }, websocket)
        else:
            await manager.send_personal({
                "type": "error",
                "message": "Unknown queue command. Try: list, add, rm, edit, clear"
            }, websocket)
    else:
        await manager.send_personal({
            "type": "error",
            "message": "Unknown command"
        }, websocket)

async def handle_chat(content: str, websocket: WebSocket):
    """Handle chat messages with AI model"""
    try:
        from models.router import ModelRouter
        model_router = ModelRouter()
        
        response = await model_router.chat(content)
        
        await manager.send_personal({
            "type": "chat_response",
            "message": response
        }, websocket)
    except Exception as e:
        await manager.send_personal({
            "type": "error",
            "message": f"Chat error: {str(e)}"
        }, websocket)
