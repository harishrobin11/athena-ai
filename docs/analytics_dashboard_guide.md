# Athena AI — Analytics Dashboard Overview & Usage Guide

## Executive Summary
The **Athena AI Analytics Dashboard** provides real-time operational visibility, system health telemetry, resource utilization analytics, and multi-tenant department governance for the Athena Enterprise AI platform.

---

## Key Functions & Business Value

### 1. Real-Time Telemetry & System Health
* **Live WebSocket Telemetry (`/api/v1/metrics/live`):** Constantly streams live system vitals directly from the Python backend and Redis broker to the UI without requiring page reloads.
* **Latency Monitoring (ms):** Real-time time-series graphing tracks API response times, enabling DevOps and IT administrators to identify bottlenecks or LLM provider latency spikes immediately.

---

## Operational KPIs (Key Performance Indicators)

| Metric | Description | Business Purpose |
| :--- | :--- | :--- |
| 🤖 **Active Agents** | Number of autonomous AI workers currently executing background tasks. | Monitors concurrency and workload distribution across Celery/FastAPI task queues. |
| 💾 **System Memory (GB)** | Real-time RAM/VRAM consumption across Vector Databases (Qdrant/Chroma), Redis, and backend processes. | Prevents Out-Of-Memory (OOM) failures and aids capacity planning. |
| ⚡ **Avg Latency (ms)** | End-to-end response time for agent generation and document retrieval. | Ensures SLA compliance for business users interacting with the assistant. |
| ⚡ **Total Executions** | Cumulative counter of all automated tasks and workflow steps completed. | Quantifies enterprise ROI and automation volume over time. |

---

## Governance & Cost Allocation

### 1. Token Usage by Department
Tracks LLM token consumption across operational business units (Finance, Legal, HR, Engineering, Sales):
* **Cost Center Attribution:** Allows enterprise administrators to attribute LLM API bills to specific departments.
* **Quota Management:** Helps set rate limits and budgets for high-volume units.

### 2. Workflow Execution Stability
Visualizes success vs. failure rates for automated business processes:
* **Failure Alerting:** Highlights broken third-party integrations, invalid API keys, or failing prompt chains.
* **Reliability Metrics:** Ensures enterprise workflows maintain an 85%+ success threshold.

---

## When to Use the Analytics Dashboard

1. **Daily Operations:** Monitor active AI agents and ensure zero system downtime.
2. **Performance Auditing:** Investigate slow queries or high latency spikes during peak business hours.
3. **Monthly Financial Review:** Audit token usage across Finance, Legal, and Engineering to optimize AI infrastructure budgets.
