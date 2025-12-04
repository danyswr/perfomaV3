# Performa - Autonomous CyberSec AI Agent System

## Overview
Performa is an autonomous cybersecurity AI agent system designed for security assessments, real-time monitoring, and automated threat detection. It features a sophisticated Next.js frontend, a Go (Fiber) backend for infrastructure, and a Python AI Intelligence service (Agent Brain) for all cognitive and mission management operations. The project aims to provide a powerful, efficient, and user-friendly platform for managing complex security tasks.

## Recent Updates (Dec 4, 2025 - Latest)
- **Clean Architecture Restructure**: Complete separation of concerns with clear responsibilities
  - **Python Agent Brain (port 8001)**: ALL intelligence and mission logic
    - Mission configuration and management
    - Agent creation and lifecycle management
    - Session save/load operations
    - AI reasoning and decision making
    - Endpoints: /api/mission/*, /api/agents/*, /api/config/*, /api/session/*, /api/start, /api/stop
  - **Go Backend (port 8000)**: Infrastructure only
    - System resource monitoring (/api/resources)
    - AI model API connections (/api/models/*)
    - Security findings management (/api/findings/*)
    - WebSocket for real-time updates (/ws/*)
    - Proxy to Python brain service for all intelligence operations
  - **Next.js Frontend (port 5000)**: User interface with real-time updates
- **Simplified Docker Setup**: Single unified Dockerfile and docker-compose.yml
- **Proxy Architecture**: Go backend proxies intelligence endpoints to Python brain

## Previous Updates (Dec 2, 2025)
- **Agent Brain Intelligence Service**: Python service for AI reasoning
  - Chain-of-thought reasoning engine
  - Cognitive processing with fine-tuned LoRA adapters
  - Decision making and strategy generation
  - Knowledge base for learned patterns
  - Endpoints: /brain/think, /brain/classify, /brain/evaluate, /brain/strategy
- **LoRA Fine-Tuned Models**: Integrated custom LoRA adapters for threat classification
  - Multiple adapter configs based on distilbert-base-uncased and roberta-base
  - Models stored in `agent-brain/models/`

## Previous Updates (Dec 2, 2025)
- **Go Backend Migration**: Complete backend rewrite from Python FastAPI to Go with Fiber web framework
  - Improved performance and lower memory footprint
  - All REST API endpoints ported: agents, resources, findings, models, missions, logs
  - WebSocket support for real-time updates and bidirectional communication
  - OpenRouter AI model integration for multi-model support
  - Go modules located in `backend-go/` directory

## Previous Updates (Dec 1, 2025)
- **Enhanced Mission Summary Dialog**: AI-powered mission summary generation with:
  - Animated progress bar (0-100%) with stage descriptions
  - Progress stages: Collecting logs, Analyzing history, Processing findings, Generating summary, Formatting, Finalizing
  - Stats grid showing findings count, log entries, and duration during generation
  - "Save to Findings" button to persist summary as markdown file
  - Fully responsive layout for mobile/small screens
- **Save Findings Summary Endpoint**: POST /api/findings/summary saves mission summaries as markdown files with timestamp
- **Responsive FileViewer Dialog**: Improved file viewer with better mobile support (95vw width, responsive text sizes)
- **Config Load Enhancement**: handleLoadConfig now properly restores instructionDelayMs and modelDelayMs fields

## Previous Updates (Dec 1, 2025)
- **Configurable Delays**: Added `model_delay_ms` and `instruction_delay_ms` settings for configurable delays before AI model response and instruction execution
  - Model delay: Sleep before calling AI model API (useful for rate limiting)
  - Instruction delay: Sleep before executing tool commands (useful for simulating slower execution)
- **Tool Restrictions Enhanced**: Backend worker enforces tool restrictions based on user-selected tools in mission config
  - When `allowed_tools_only=True` and `requested_tools` is empty, ALL tools are blocked
  - When `allowed_tools_only=True` with tools specified, only those tools are allowed
- **New Database Models**: Added for persistent storage
  - `MissionConfig`: Reusable mission configurations with delay settings
  - `AgentMemoryStore`: Database-backed agent memory (more efficient than in-memory)
  - `AgentLogEntry`: Real-time agent log entries for streaming
  - `ToolPermission`: Tool permissions per mission/agent
- **Docker Improvements**: Complete Docker setup ready for deployment (adapted to Replit's Nix environment)
  - Separate Dockerfiles for frontend/backend with proper build optimization
  - `BACKEND_URL` routing for Docker network service discovery
  - Health checks for postgres, backend, and frontend services
  - Volume mounts for findings, logs, and agent memory persistence
- **Mission Config Delay Settings**: Fully integrated delay timing in mission config save/load
- **Fixed Dependencies**: Added missing `react-is` dependency for recharts module

## Previous Updates (Nov 30, 2025 - Final)
- **Docker Connectivity Fixed**: Next.js config now respects `BACKEND_URL` env var for proper Docker network routing
- **start.sh Permission Fixes**: Auto-clean logs/findings with `chmod 777` to prevent permission locks from sudo usage
- **Replit Environment Support**: start.sh now handles both venv and Replit's native `.pythonlibs` Python environment
- **Backend Config**: Pydantic v2 config now ignores extra env vars (frontend-only vars won't crash backend)
- **WebSocket Smart Detection**: use-websocket.ts derives endpoint from `NEXT_PUBLIC_API_URL` environment variable

## Previous Updates (Nov 30, 2025)
- **Save Mission Config**: Save button now saves full mission configuration (target, AI models, custom instructions, tools) to both localStorage and backend SQLite database
- **Per-Agent Real-time Logs**: Findings Explorer now has "Agents" tab showing individual logs for each agent with filtering by agent ID
- **Custom Instructions Scrollbar**: Added max-height (200px) and scrollable area to custom instructions textarea to prevent layout issues
- **Tool Restrictions Enforced**: Backend worker properly blocks tools not in user-selected list when allowedToolsOnly is enabled
- **Break State for Agents**: Added blue "break" status when agents are waiting for AI model response or rate limit cooldown, with reason display
- **Rate Limit Toggle**: Added toggle switch to enable/disable rate limiting with configurable 1-10 requests per second slider
- **Execution Duration**: Added comprehensive duration options (5, 10, 15, 20, 30, 60, 120 min, custom, unlimited) with auto-stop when expired
- **Tools Restriction**: New "allowedToolsOnly" feature to restrict agents to only use user-selected tools from categories (network_recon, web_scanning, vuln_scanning, osint, system_info)
- **Config Sidebar Tabs**: Reorganized config sidebar with Basic, Advanced, and Tools tabs for better UX
- **Unified MissionConfig**: Aligned MissionConfig interface across frontend and backend for consistent data flow
- **Enhanced Mission Config**: Added batch size slider (5-30), rate limit control (0.1-5.0 RPS), and execution duration options (10-60 min or unlimited)
- **Priority Tools System**: Users can specify priority tools that agents will prefer during scanning
- **Grid/List View Toggle**: Active Agents section now supports grid and list view modes for better visualization
- **PostgreSQL Database Integration**: Added database models for missions, agents, findings, chat history, and activities
- **Docker Deployment**: Complete Docker/docker-compose setup for containerized deployment
- **Findings Explorer**: Real-time file browser showing findings organized by target with JSON/TXT/PDF viewer popup
- **Resizable Sidebar**: Drag-to-resize sidebar with localStorage persistence
- **Tool Request Feature**: New "Tools" tab in Mission Config for priority tool selection
- **Enhanced Chat**: Improved WebSocket connection handling and error display
- **Real-time Directory Watcher**: Backend monitors findings folder and broadcasts updates via WebSocket

## User Preferences
- Clean, organized findings (no HTML clutter)
- Separate folders for each target
- TXT/JSON/PDF reports only
- Real-time event broadcasting with clear labels
- History limited to 15 recent items (not overwhelming)
- Token-efficient model output (batch commands)

## System Architecture
The system employs a three-tier architecture with a Next.js frontend, Go backend for real-time operations, and Python AI Intelligence service.

### Frontend (Next.js 16.0.3) - Port 5000
- **Framework**: Next.js with React 19 and TypeScript.
- **UI/UX**: Utilizes Radix UI, Tailwind CSS, and shadcn/ui for a modern and responsive interface.
- **Features**: Real-time event broadcast history, live chat, per-agent resource graphs (CPU/Memory), mission timer, OS configuration, and a security findings panel with severity tracking.
- **Networking**: Configured for Replit's proxy environment with Next.js rewrites for API proxying to the backend.

### Backend (Go with Fiber) - Port 8000
- **Framework**: Go with Fiber web framework (high-performance, Express-like).
- **Structure**: Organized into packages: `config/`, `handlers/`, `models/`, `openrouter/`, `ws/`, `brain/`.
- **Core Components**: Manages multi-agent operations, WebSocket communication for real-time events, resource monitoring with psutil integration.
- **AI Integration**: OpenRouter client for access to various AI models (GPT-4, Claude, Gemini, Llama), with optional direct API fallbacks for Anthropic and OpenAI.
- **Brain Integration**: HTTP client to communicate with Python Agent Brain service for cognitive operations.
- **Memory Management**: In-memory data structures for agents, findings, and mission state.
- **Concurrency**: Uses Go's goroutines and channels for efficient concurrent operations.
- **Findings Organization**: Organizes findings by target name into dedicated folders, with file explorer endpoints for browsing.

### Agent Brain (Python FastAPI) - Port 8001
- **Framework**: Python with FastAPI and uvicorn.
- **Structure**: Organized into modules: `core/`, `memory/`, `reasoning/`, `models/`, `api/`.
- **Core Components**:
  - **AgentBrain**: Central intelligence controller for reasoning and decision making
  - **CognitiveEngine**: Processes inputs using fine-tuned LoRA models
  - **DecisionMaker**: Strategic planning and action selection
  - **ReasoningAnalyzer**: Deep analysis of tasks and contexts
  - **ChainOfThought**: Multi-step reasoning for complex problems
- **AI Models**: Fine-tuned LoRA adapters (distilbert-base-uncased, roberta-base) for threat classification
- **Knowledge Base**: Persistent storage for learned patterns and successful strategies
- **Context Management**: Working memory for maintaining agent state across operations

### System Design Choices
- **Real-time Updates**: WebSocket broadcasts provide real-time updates for events, instruction queues, and findings.
- **Instruction Queue**: A global, shared instruction queue (thread-safe with asyncio locks) allows agents to compete for and execute instructions efficiently.
- **Batch Processing**: AI models generate commands in batches (configurable 5-30 items) to optimize token usage and reduce API calls.
- **Rate Limiting**: User-configurable rate limiting (0.1-5.0 requests per second) prevents API throttling and rate limit errors.
- **Execution Duration**: Missions can run for a specified duration (10, 20, 30, 60 minutes) or until manually stopped.
- **Agent Orchestration**: Features a per-agent queue distribution system and robust command validation against an extensive registry of 368+ security tools.
- **Security**: Includes a dangerous command blocklist to prevent harmful operations.
- **Memory Optimization**: Strict limits on memory components like `context_history`, `execution_history`, `message queue`, and `shared discoveries` ensure bounded memory growth.
- **Database Persistence**: PostgreSQL database stores missions, agents, findings, chat history, and activities for long-term tracking and analysis.

## External Dependencies

### Go
- `github.com/gofiber/fiber/v2`: High-performance web framework.
- `github.com/gofiber/websocket/v2`: WebSocket support for Fiber.
- `github.com/shirou/gopsutil/v3`: Cross-platform system resource monitoring.
- `github.com/google/uuid`: UUID generation for agents and findings.

### Node.js
- `next`, `react`, `react-dom`: Frontend framework.
- `@radix-ui/*`: UI component primitives.
- `tailwindcss`: Utility-first CSS framework.
- `lucide-react`: Icon library.
- `recharts`: Data visualization library.

### Third-party Services
- **OpenRouter**: Primary AI model provider, supporting various models like GPT-4, Claude, Gemini, and Llama.