FROM golang:1.22-alpine AS go-builder

WORKDIR /build

RUN apk add --no-cache git

COPY backend-go/go.mod backend-go/go.sum ./backend-go/
WORKDIR /build/backend-go
RUN go mod download

COPY backend-go/ .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o performa-backend .


FROM node:20-alpine AS frontend-deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps


FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY --from=frontend-deps /app/node_modules ./node_modules
COPY . .

RUN rm -rf backend-go agent-brain

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build


FROM python:3.11-slim AS brain

WORKDIR /app/brain

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY agent-brain/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent-brain/ .
RUN mkdir -p /app/brain/knowledge /app/brain/models /app/brain/data

ENV BRAIN_HOST=0.0.0.0
ENV BRAIN_PORT=8001


FROM python:3.11-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tzdata \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=go-builder /build/backend-go/performa-backend /app/backend/performa-backend
COPY --from=brain /app/brain /app/brain
COPY --from=brain /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=frontend-builder /app/public /app/frontend/public
COPY --from=frontend-builder /app/.next/standalone /app/frontend/
COPY --from=frontend-builder /app/.next/static /app/frontend/.next/static

RUN mkdir -p /app/logs /app/findings /app/brain/knowledge /app/brain/models /app/brain/data

COPY <<EOF /etc/supervisor/conf.d/performa.conf
[supervisord]
nodaemon=true
logfile=/app/logs/supervisord.log
pidfile=/var/run/supervisord.pid

[program:brain]
command=python /app/brain/main.py
directory=/app/brain
autostart=true
autorestart=true
stdout_logfile=/app/logs/brain.log
stderr_logfile=/app/logs/brain-error.log
environment=BRAIN_HOST="0.0.0.0",BRAIN_PORT="8001"

[program:backend]
command=/app/backend/performa-backend
directory=/app/backend
autostart=true
autorestart=true
stdout_logfile=/app/logs/backend.log
stderr_logfile=/app/logs/backend-error.log
environment=HOST="0.0.0.0",PORT="8000",LOG_DIR="/app/logs",FINDINGS_DIR="/app/findings",BRAIN_SERVICE_URL="http://localhost:8001"

[program:frontend]
command=node /app/frontend/server.js
directory=/app/frontend
autostart=true
autorestart=true
stdout_logfile=/app/logs/frontend.log
stderr_logfile=/app/logs/frontend-error.log
environment=NODE_ENV="production",PORT="5000",HOSTNAME="0.0.0.0"
EOF

ENV HOST=0.0.0.0
ENV PORT=8000
ENV BRAIN_PORT=8001
ENV FRONTEND_PORT=5000
ENV LOG_DIR=/app/logs
ENV FINDINGS_DIR=/app/findings
ENV BRAIN_SERVICE_URL=http://localhost:8001

EXPOSE 5000 8000 8001

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/performa.conf"]
