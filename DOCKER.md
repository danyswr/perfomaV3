# Performa - Docker Deployment

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Setup

1. **Create environment file:**
```bash
cp .env.example .env
```

2. **Edit `.env` and add your API keys:**
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

3. **Build and start all services:**
```bash
docker-compose up -d --build
```

4. **Access the application:**
- Frontend: http://localhost:5000
- Backend API: http://localhost:8000
- Brain Service: http://localhost:8001

### Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 5000 | Next.js web interface |
| backend | 8000 | Go API server (Fiber) |
| brain | 8001 | Python AI intelligence service |

### Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f brain

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

### Volume Mounts

The following directories are mounted as volumes for persistence:
- `./logs` - Application logs
- `./findings` - Security findings output
- `./agent-brain/knowledge` - AI knowledge base
- `./agent-brain/models` - LoRA model files

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| OPENROUTER_API_KEY | backend | API key for OpenRouter AI models |
| BACKEND_URL | frontend | Internal URL for backend service |
| BRAIN_SERVICE_URL | backend | Internal URL for brain service |
| NEXT_PUBLIC_API_URL | frontend | Public API URL (for browser) |
| NEXT_PUBLIC_WS_URL | frontend | Public WebSocket URL |

### Troubleshooting

**Backend won't start:**
```bash
docker-compose logs backend
```

**Frontend can't connect to backend:**
- Ensure backend is healthy: `docker-compose ps`
- Check network: `docker network ls`

**Permission issues with volumes:**
```bash
chmod -R 777 logs findings
```
