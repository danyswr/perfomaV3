# Autonomous CyberSec AI Agent System

Backend system untuk autonomous AI agents yang melakukan cyber security assessment.

## Features

- ✅ Multi-agent orchestration (max 10 agents)
- ✅ Real-time WebSocket communication
- ✅ Live chat dengan AI model
- ✅ Command queue management
- ✅ Resource monitoring (CPU, RAM, Network)
- ✅ Stealth & Aggressive modes
- ✅ Agent collaboration & knowledge sharing
- ✅ Automatic logging & reporting
- ✅ Findings classification (Critical/High/Medium/Low/Info)
- ✅ Export ke PDF/HTML/JSON

## Installation

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Copy `.env.example` to `.env` dan configure:
\`\`\`bash
cp .env.example .env
\`\`\`

3. Edit `.env` dengan API keys Anda:
\`\`\`
OPENROUTER_API_KEY=your_openrouter_key_here
\`\`\`

## Running

\`\`\`bash
python main.py
\`\`\`

Server akan running di `http://localhost:8000`

## API Endpoints

### REST API

- `POST /api/start` - Start operation dengan agents
- `GET /api/agents` - Get semua agents
- `GET /api/agents/{id}` - Get specific agent
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/agents/{id}/pause` - Pause agent
- `POST /api/agents/{id}/resume` - Resume agent
- `GET /api/resources` - Get system resources
- `GET /api/findings` - Get all findings
- `GET /api/models` - Get available models

### WebSocket

- `WS /ws/live` - Live chat & updates

## WebSocket Commands

### Chat Mode
\`\`\`
/chat
\`\`\`

### Queue Management
\`\`\`
/queue list
/queue add {"1": "RUN nmap -sV target.com"}
/queue rm 1
/queue edit 1 {"1": "RUN nikto -h target.com"}
\`\`\`

## Agent Commands

Agents menggunakan format khusus untuk komunikasi:

### Execute Command
\`\`\`
RUN nmap -sV target.com
\`\`\`

### Batch Commands (hemat token)
\`\`\`json
{
  "1": "RUN nmap -sV target.com",
  "2": "RUN nikto -h target.com",
  "3": "RUN whatweb target.com"
}
\`\`\`

### Save Findings
\`\`\`
<write>
IP Address: 192.168.1.1
Open Ports: 80, 443, 22
Vulnerabilities: SSH weak encryption
</write>
\`\`\`

### Signal Completion
\`\`\`
<END!>
\`\`\`

## Architecture

\`\`\`
backend/
├── server/          # FastAPI server & WebSocket
├── models/          # AI model integration
├── agent/           # Agent orchestration
├── monitor/         # Logging & resource monitoring
├── logs/            # Log files
└── findings/        # Security findings & reports
\`\`\`

## Configuration

Edit `.env` untuk customize:

- `MAX_AGENTS`: Maximum agents (default: 10)
- `MAX_MEMORY_PERCENT`: Auto-pause threshold (default: 80%)
- `DEFAULT_DELAY_MIN/MAX`: Rate limiting delays
- `ENABLE_PROXY`: Enable proxy support untuk stealth

## Security Tools Support

- nmap - Network scanning
- nikto - Web vulnerability scanner  
- sqlmap - SQL injection testing
- dirb/dirbuster - Directory enumeration
- whatweb - Web technology identification
- Dan tools lainnya

## Output

### Logs
`logs/agent_system_YYYYMMDD.log` - All events

### Findings  
`findings/findings_YYYYMMDD.txt` - Security findings

### Reports
- `findings/report_YYYYMMDD_HHMMSS.html` - HTML report
- `findings/report_YYYYMMDD_HHMMSS.json` - JSON export

## Tips

1. Gunakan stealth mode untuk scanning yang lebih pelan dan tidak terdeteksi
2. Batch commands untuk menghemat token AI
3. Monitor resource usage untuk cegah overload
4. Agents akan collaborate dan share findings otomatis
5. Gunakan live chat untuk kasih guidance tambahan saat operation berjalan

## Troubleshooting

- **Rate limit errors**: Increase delay di `.env`
- **Memory issues**: Reduce `MAX_AGENTS` atau increase `MAX_MEMORY_PERCENT`
- **API errors**: Check OpenRouter API key di `.env`
- **Tool not found**: Install required security tools (nmap, nikto, etc.)

## Development

Ini adalah project tugas akhir. Feel free untuk extend dan customize sesuai kebutuhan!
