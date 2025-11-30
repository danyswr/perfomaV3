# Performa - Autonomous CyberSec AI Agent System

## Overview
Performa is an autonomous cybersecurity AI agent system designed for security assessments, real-time monitoring, and automated threat detection. It features a sophisticated Next.js frontend and a Python FastAPI backend, leveraging multi-agent AI capabilities to enhance cybersecurity operations. The project aims to provide a powerful, efficient, and user-friendly platform for managing complex security tasks.

## Recent Updates (Nov 30, 2025)
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
The system employs a multi-agent architecture with a Next.js frontend and a Python FastAPI backend.

### Frontend (Next.js 16.0.3)
- **Framework**: Next.js with React 19 and TypeScript.
- **UI/UX**: Utilizes Radix UI, Tailwind CSS, and shadcn/ui for a modern and responsive interface.
- **Features**: Real-time event broadcast history, live chat, per-agent resource graphs (CPU/Memory), mission timer, OS configuration, and a security findings panel with severity tracking.
- **Networking**: Configured for Replit's proxy environment with Next.js rewrites for API proxying to the backend.

### Backend (Python FastAPI)
- **Framework**: FastAPI with Uvicorn.
- **Core Components**: Manages multi-agent operations, WebSocket communication for real-time events, resource monitoring, and batch command generation/execution.
- **AI Integration**: Primarily uses OpenRouter for access to various AI models (GPT-4, Claude, Gemini, Llama), with optional direct API fallbacks for Anthropic and OpenAI.
- **Memory Management**: Employs an SQLite-based persistent memory system for conversation history, findings, and knowledge base storage, utilizing `aiosqlite` for async operations.
- **Collaboration**: Features an inter-agent collaboration system with a message bus for communication, shared knowledge, and discovery sharing.
- **Throttling & Rate Limiting**: Includes an intelligent throttling mechanism (`ThrottleLevel` enum) and token bucket algorithm-based rate limiting for AI model calls to prevent API errors.
- **Findings Organization**: Organizes findings by target name into dedicated folders, generating clean TXT, JSON, and PDF reports.

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

### Python
- `fastapi`, `uvicorn`: Web framework and ASGI server.
- `websockets`: Real-time communication.
- `psutil`: System resource monitoring.
- `httpx`, `aiohttp`: HTTP clients.
- `sqlalchemy`, `aiosqlite`: Database ORM and async SQLite.
- `reportlab`, `matplotlib`, `weasyprint`: Report generation.
- `openai`, `anthropic`: AI model integrations.

### Node.js
- `next`, `react`, `react-dom`: Frontend framework.
- `@radix-ui/*`: UI component primitives.
- `tailwindcss`: Utility-first CSS framework.
- `lucide-react`: Icon library.
- `recharts`: Data visualization library.

### Third-party Services
- **OpenRouter**: Primary AI model provider, supporting various models like GPT-4, Claude, Gemini, and Llama.