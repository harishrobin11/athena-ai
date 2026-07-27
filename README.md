# 🌟 Athena AI

<p align="center">
  <strong>Enterprise AI Platform for Intelligent Finance Operations & Multi-Agent Orchestration</strong>
</p>

<p align="center">
  <a href="https://github.com/harishrobin11/athena-ai">
    <img src="https://img.shields.io/badge/Author-Harish%20Robin%20H-orange.svg?style=flat&logo=github" alt="Author: Harish Robin H" />
  </a>
  <a href="https://github.com/harishrobin11/athena-ai/actions/workflows/ci.yml">
    <img src="https://github.com/harishrobin11/athena-ai/actions/workflows/ci.yml/badge.svg" alt="Continuous Integration Status" />
  </a>
  <a href="https://github.com/harishrobin11/athena-ai/actions/workflows/ci-cd.yml">
    <img src="https://img.shields.io/badge/CI%2FCD-Pipeline-brightgreen.svg" alt="CI/CD Pipeline" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18.0+-61DAFB.svg?style=flat&logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Multi-Agent Execution Pipeline](#-multi-agent-execution-pipeline)
- [Repository Structure](#-repository-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Configuration](#environment-configuration)
  - [Deployment via Docker Compose](#deployment-via-docker-compose)
  - [Local Development Setup](#local-development-setup)
- [API Documentation](#-api-documentation)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Observability & Monitoring](#-observability--monitoring)
- [License](#-license)

---

## 🚀 Overview

**Athena AI** is an enterprise-grade AI automation platform designed for financial operations, intelligent document processing, compliance tracking, and autonomous multi-agent task execution. Powered by **LangGraph**, **FastAPI**, **React/Vite**, **ChromaDB/Qdrant**, and **Celery**, Athena AI enables seamless multi-tenant collaboration, hybrid RAG document search, and real-time operational telemetry.

---

## ✨ Key Features

- 🧠 **Multi-Agent Orchestration**: Built on LangGraph state machines featuring supervisor-worker routing, execution plan synthesis, and dynamic fallback handling.
- 🔍 **Hybrid RAG Retrieval Engine**: Combines BM25 term scoring, dense vector embeddings, and **FlashRank (MiniLM)** neural re-ranking for ultra-precise document retrieval.
- 💼 **Intelligent Financial Tools**: ML-powered expense classification, financial invoice parsing, ledger auditing, and interactive diagram synthesis.
- 🔒 **Enterprise Multi-Tenancy & Security**: Strict workspace boundaries, JWT role-based access control (RBAC), bcrypt credential hashing, and encrypted payloads.
- ⚡ **Asynchronous Background Processing**: Celery distributed workers backed by Redis for offloading heavy OCR, document loading, and model inference.
- 📊 **Real-time Telemetry & Observability**: OpenTelemetry instrumentation, Prometheus metric scraping, and pre-built Grafana dashboards.
- 🛡️ **Containerized Microservices**: Orchestrated via Docker Compose with reverse proxying through Caddy and Cloudflare Tunnels.

---

## 🏗️ System Architecture

```mermaid
graph TD
    Client["Client / Web Application (React + Vite)"] --> Caddy["Reverse Proxy (Caddy / Cloudflared)"]
    Caddy --> Gateway["FastAPI Core Engine"]

    subgraph "Core Backend Services"
        Gateway --> Auth["Security & Auth (JWT/RBAC)"]
        Gateway --> Router["Unified API Gateway"]
        Router --> Orchestrator["LangGraph Supervisor Orchestrator"]
        Router --> RAG["Document & Vault Service"]
        Router --> Tools["Agentic ML & Finance Tools"]
    end

    subgraph "Data & Memory Layer"
        Orchestrator --> State["LangGraph State Manager"]
        RAG --> VectorDB["Vector Store (ChromaDB / Qdrant)"]
        Gateway --> DB["Relational DB (PostgreSQL / SQLite)"]
        Gateway --> Cache["Redis Cache & Rate Limiter"]
    end

    subgraph "Async Execution & Observability"
        Gateway --> Celery["Celery Distributed Task Worker"]
        Celery --> Storage["Cloud Storage (S3 / Azure / Local)"]
        Gateway --> Metrics["Prometheus & Grafana Telemetry"]
    end
```

---

## 🤖 Multi-Agent Execution Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Finance Manager
    participant API as FastAPI Gateway
    participant Supervisor as LangGraph Supervisor
    participant Worker as Specialized Worker Node
    participant RAG as Hybrid RAG / Vector Store
    participant Response as Final Synthesizer

    User->>API: Submit Prompt ("Analyze Q3 Server Expense Invoice")
    API->>Supervisor: Initialize AthenaAgentState
    Supervisor->>Supervisor: Generate Execution Plan & Select Worker Route
    alt Route: Document Retrieval
        Supervisor->>Worker: Dispatch to RAG Worker
        Worker->>RAG: Dense Vector Search + FlashRank Rerank
        RAG-->>Worker: Relevant Chunks & Metadata
        Worker-->>Supervisor: Synthesized Context Payload
    else Route: ML Classifier
        Supervisor->>Worker: Dispatch to Expense ML Worker
        Worker-->>Supervisor: Classification & Confidence Score
    end
    Supervisor->>Response: Aggregate Worker Outputs
    Response-->>API: Stream Final Synthesized Response
    API-->>User: Structured Answer + Financial Analytics
```

---

## 📁 Repository Structure

```
athena-ai/
├── app/                        # Main FastAPI Application
│   ├── api/                    # API Route Handlers (v1, Admin, Auth, Vault, Agent)
│   ├── core/                   # Security, Config, Logging, Celery App
│   ├── db/                     # SQLAlchemy Models, Engine Bindings & Migrations
│   ├── memory/                 # Conversation & Vector Memory Stores
│   ├── rag/                    # Loader, Splitter, Embedder, Retriever & Vector Store
│   ├── schemas/                # Pydantic Request/Response Models
│   ├── services/               # Document Service, Storage Providers
│   ├── tools/                  # Agentic ML & Financial Classification Tools
│   └── main.py                 # FastAPI Application Entrypoint
├── backend/                    # Core Backend Package Configuration
├── frontend/                   # React 18 + Vite Web Application
│   ├── src/                    # Components, Hooks, Pages, Services
│   ├── package.json            # Node Dependencies & Scripts
│   └── Dockerfile              # Production Nginx Container Build
├── tests/                      # Pytest Test Suite
│   ├── test_agent_graph.py     # LangGraph Agent Routing Tests
│   ├── test_api_health.py      # Gateway Health & Security Tests
│   ├── test_api_validation.py  # Authentication & Input Validation Tests
│   ├── test_document_fast_cache.py # Document Caching Tests
│   └── test_rag_and_diagrams.py # RAG Retrieval & Diagram Synthesis Tests
├── docker-compose.yml          # Multi-Container Service Orchestration
├── Dockerfile                  # Python 3.11 Backend Container Build
├── pyproject.toml              # Project Dependencies & Tool Configurations
└── requirements.txt            # Python Package Requirements
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** v2+
- **Python** 3.11+ (for local CLI development)
- **Node.js** 20+ & **npm** (for frontend development)

---

### Environment Configuration

Create a `.env` file in the project root:

```bash
# General Setup
ENV=production
DOMAIN_NAME=localhost
SECRET_KEY=athena_super_secret_jwt_key_2026

# Database & Cache
DATABASE_URL=postgresql://athena:athena_secure_password@postgres:5432/athena_db
REDIS_URL=redis://redis:6379

# Vector Databases
QDRANT_URL=http://qdrant:6333

# LLM Providers (Optional for Azure/Ollama)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2
```

---

### Deployment via Docker Compose

Spin up the full multi-container cluster with a single command:

```bash
docker-compose up -d --build
```

#### Running Container Services

| Service | Container Name | Host Port | Purpose |
| :--- | :--- | :--- | :--- |
| **Reverse Proxy** | `athena_caddy` | `80`, `443` | SSL Termination & Routing |
| **Core API Gateway** | `athena_backend` | Internal (`8000`) | FastAPI Application Engine |
| **Frontend UI** | `athena_frontend` | Internal (`80`) | React SPA Static Build |
| **Celery Worker** | `athena_worker` | Internal | Background Heavy Tasks |
| **PostgreSQL** | `athena_postgres` | `5432` | Primary Database |
| **Qdrant Vector DB** | `athena_qdrant` | `6333`, `6334` | Vector Indexing |
| **Redis** | `athena_redis` | `6379` | Cache & Message Broker |
| **Prometheus** | `athena_prometheus` | `9091` | Metric Aggregation |
| **Grafana** | `athena_grafana` | `3002` | Dashboard Visualizations |

---

### Local Development Setup

#### 1. Backend Setup

```bash
# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run FastAPI Development Server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```

---

## 📋 API Documentation

Once the backend is running, explore interactive API documentation at:

- **Swagger UI**: [http://localhost/api/docs](http://localhost/api/docs)
- **OpenAPI JSON**: [http://localhost/api/openapi.json](http://localhost/api/openapi.json)

### Primary API Route Groups

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Core Engine Health Check |
| `POST` | `/login` | User Authentication & JWT Generation |
| `POST` | `/register` | User Registration & Multi-Tenant Setup |
| `POST` | `/api/v1/agent/chat` | Conversational Stream Gateway |
| `POST` | `/api/v1/vault/query` | RAG Memory Document Query |
| `POST` | `/upload` | PDF & Image Document Ingestion |
| `GET` | `/metrics` | Prometheus Metrics Stream |

---

## 🧪 Testing & Quality Assurance

Athena AI uses `pytest` for backend verification and `npm` for production frontend builds.

```bash
# Run pytest test suite
pytest tests/ -v

# Run with coverage report
pytest --cov=app tests/

# Verify Frontend Production Build
cd frontend && npm run build
```

---

## 📊 Observability & Monitoring

Athena AI includes out-of-the-box observability:

- **Grafana Dashboards**: Navigable at `http://localhost:3002` (Default User: `admin` / Password: `admin`).
- **Prometheus Metric Scraper**: Accessible at `http://localhost:9091`.
- **OpenTelemetry Instrumentation**: Automatically tracks incoming HTTP request latency, status codes, and execution durations.

---

## 👤 Author & Maintainer

**Harish Robin H**
- **GitHub**: [@harishrobin11](https://github.com/harishrobin11)
- **Project Repository**: [harishrobin11/athena-ai](https://github.com/harishrobin11/athena-ai)

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  Architected & Developed with ❤️ by <strong><a href="https://github.com/harishrobin11">Harish Robin H</a></strong>
</p>