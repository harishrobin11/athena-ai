#!/usr/bin/env bash
set -e

echo "=========================================="
echo "   Athena AI MVP - Single-Command Deploy   "
echo "=========================================="

# 1. Environment File Verification
if [ ! -f .env ]; then
    echo "[!] .env file not found. Initializing from .env.example template..."
    cp .env.example .env
    echo "[✓] Created .env file. Customize model keys and secrets as needed."
else
    echo "[✓] Found existing .env file."
fi

# 2. Git Synchronization
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[*] Pulling latest repository updates..."
    git pull origin main --rebase || echo "[!] Notice: Git pull skipped or active branch differs."
fi

# 3. Build & Orchestrate Microservices
echo "[*] Launching containers with volume persistence via Docker Compose..."
docker compose up -d --build --remove-orphans

# 4. Status Overview
echo ""
echo "=========================================="
echo "   Athena AI MVP Deployment Complete!     "
echo "=========================================="
docker compose ps

echo ""
echo "[✓] Microservice Access Endpoints:"
echo "    - Frontend & API Gateway (Caddy HTTPS): http://localhost"
echo "    - Vector Database (Qdrant): http://localhost:6333"
echo "    - Relational DB (PostgreSQL): localhost:5432"
echo "    - Memory Cache & Queue (Redis): localhost:6379"
