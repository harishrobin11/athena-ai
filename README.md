# 🚀 Athena AI (v2.0 Enterprise Intelligence)

> The Ultimate Enterprise Knowledge Platform for Intelligent Operations

---

## Status

🚀 **Phase 6 Completed: Enterprise Intelligence Engine is LIVE**

---

## Vision

Athena AI is a production-grade Enterprise AI Platform that combines:

- LLM Orchestration via LangGraph
- Advanced Neural Re-ranking & Contextual RAG
- Visual Prompt Studio & Dynamic Workflow Testing
- Durable NLP (Fast Offline NER & Sentiment)
- Safety Interception Guardrails (PII Masking & Injection Filtering)
- Multi-Tenant Security & Isolation
- Distributed Caching & OpenTelemetry Observability

to automate enterprise workflows effortlessly and securely.

---

## Architecture & Deployment

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Streamlit
- **Databases**: PostgreSQL (Relational), Neo4j (Graph), ChromaDB (Vector), Redis (Cache)
- **Deployment Topology**: 
  - Docker Multi-stage Containerization
  - Kubernetes (HPA scaling, Deployments, Services)
  - GitHub Actions CI/CD (Trivy Scans, Linting)

---

## Quickstart (Local Docker)

The entire environment (including NLP models and OCR bindings) is fully containerized.

```bash
# Build the production image (this will download spacy models inside the container)
docker build -t athena-ai .

# Run the backend and frontend simultaneously
docker run -p 8000:8000 -p 8501:8501 athena-ai
```

---

## License