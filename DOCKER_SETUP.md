# Docker Setup Guide - Performa

## Quick Start (3 Langkah Mudah)

### 1. Persiapan
```bash
# Clone atau masuk ke project directory
cd /path/to/performa

# Pastikan Docker installed
docker --version
docker-compose --version
```

### 2. Jalankan Docker
```bash
# Build dan run services (Docker 29+ menggunakan 'docker compose' tanpa hyphen)
docker compose up --build

# Atau jika sudah built sebelumnya (lebih cepat):
docker compose up
```

### 3. Akses Aplikasi
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Commands Penting

### Start Services
```bash
# Jalankan di foreground (lihat logs)
docker compose up

# Jalankan di background
docker compose up -d

# Rebuild jika ada perubahan kode
docker compose up --build
```

### Stop Services
```bash
# Stop semua services
docker compose down

# Stop dan hapus volumes (database data)
docker compose down -v
```

### View Logs
```bash
# Lihat logs semua services
docker compose logs

# Lihat logs backend saja
docker compose logs backend

# Follow logs real-time
docker compose logs -f
```

### Rebuild Services
```bash
# Rebuild image
docker compose build

# Rebuild tanpa cache
docker compose build --no-cache
```

---

## Environment Variables

Buat file `.env` di root directory:

```env
# PostgreSQL
DATABASE_URL=postgresql://user:password@postgres:5432/performa
PGUSER=user
PGPASSWORD=password
PGDATABASE=performa
PGHOST=postgres
PGPORT=5432

# API Keys
OPENROUTER_API_KEY=your_key_here
ANTHROPIC_API_KEY=optional
OPENAI_API_KEY=optional

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Struktur Docker

```
Docker Setup terdiri dari:
├── Frontend (Node.js + Next.js)
│   └── Port 5000
├── Backend (Python + FastAPI)
│   └── Port 8000
└── Database (PostgreSQL)
    └── Port 5432
```

---

## Troubleshooting

### Port already in use
```bash
# Kill process di port tertentu
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Database connection error
```bash
# Reset database
docker compose down -v
docker compose up --build
```

### Check container status
```bash
docker compose ps
```

### SSH ke container
```bash
# Ke backend
docker compose exec backend bash

# Ke frontend
docker compose exec frontend sh

# Ke database
docker compose exec postgres psql -U user -d performa
```

---

## Performance Tips

1. **Use .dockerignore** - Skip unnecessary files
2. **Layer caching** - Rebuild hanya image yang berubah
3. **Volumes** - Persist data dengan PostgreSQL volume
4. **Network** - Services terhubung otomatis via docker-compose network

---

## Deploy ke Production

### Using Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.prod.yml performa
```

### Using Kubernetes
```bash
kubectl apply -f k8s/
```

---

## Helpful Commands

```bash
# View resource usage
docker stats

# Clean up unused images
docker image prune

# Remove all containers
docker-compose down --remove-orphans

# Full reset
docker-compose down -v && docker system prune -a
```

---

**Happy Scanning!** 🚀
