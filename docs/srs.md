# Software Requirements Specification (SRS) — Aether AI Automation Platform

This Software Requirements Specification document details the functional, architectural, security, and performance requirements for the Aether AI Automation Platform.

---

## 1. Introduction

### 1.1 Purpose
Aether is an extensible, private-first personal AI automation platform designed to run securely on user-controlled containerized environments. It coordinates local system operations, schedules tasks, manages long-term user memories, orchestrates autonomous agents, and integrates with third-party productivity tools (Calendar, Email, Chat).

### 1.2 System Operations Boundaries
* **Core Platform**: FastAPI REST backend server and Next.js frontend web workspace.
* **Worker Queue**: Redis queue message broker coordinating Celery asynchronous workers.
* **Datastores**: PostgreSQL (relational schemas metadata), ChromaDB (long-term vector memory embeddings), and MinIO (object storage).
* **Proxy Router**: Nginx routing proxy.

---

## 2. Architecture & Component Blueprint

```
+-------------------------------------------------------------------+
|                            Nginx Proxy                            |
+-------------------------------------------------------------------+
       | (Port 80 -> /)                           | (Port 80 -> /v1/*)
       v                                          v
+------------------+                       +------------------------+
| Next.js Web App  |                       |  FastAPI Backend API   |
+------------------+                       +------------------------+
                                                       |
                       +-------------------------------+-------------------------------+
                       |                               |                               |
                       v                               v                               v
            +--------------------+           +--------------------+         +--------------------+
            |    PostgreSQL      |           |     Redis Queue    |         |      ChromaDB      |
            | (Relational Meta)  |           |   (Celery Broker)  |         | (Vector Memories)  |
            +--------------------+           +--------------------+         +--------------------+
                       ^                               |                               ^
                       |                               v                               |
                       |                     +--------------------+                    |
                       +---------------------|   Celery Worker    |--------------------+
                                             +--------------------+
                                                       |
                                                       v
                                             +--------------------+
                                             |   MinIO Storage    |
                                             +--------------------+
```

---

## 3. Functional Requirements

### 3.1 Long-Term Memory (LTM)
* **LTM-001**: Aether must provide a vector memory store for semantic search and retrieval of user preferences.
* **LTM-002**: Users must be able to view, edit, and delete stored memories.
* **LTM-003**: The system must enforce opt-in consent for storing new memories.

### 3.2 Visual Workflow Builder
* **WKB-001**: The system must provide a node-based visual drag-and-drop workspace for designing task flows.
* **WKB-002**: Workflows must support multiple trigger nodes (scheduled cron, event-driven hooks) and action nodes (LLM calls, CLI commands).
* **WKB-003**: The backend execution engine must validate graph syntax to prevent dependency loops.

### 3.3 Safety & Approval Gateway
* **APG-001**: High-risk outbound operations (sending email drafts, posting to Slack, scheduling calendar events) must be suspended as "proposals" in an outbox queue.
* **APG-002**: Suspended operations must execute only after explicit human approval via the web UI.

### 3.4 Autonomous AI Agents
* **AGT-001**: The agent orchestration engine must enforce strict execution limits (budget thresholds, step counts, and time boundaries).
* **AGT-002**: Agents must only execute commands and access file paths within their designated workspace sandboxes.

### 3.5 Third-Party Integrations
* **INT-001**: Secure OAuth credential management must segment authorization scopes for Google Calendar, Gmail, and Slack.
* **INT-002**: Synchronizers must periodically sync new inbox messages and calendar invites.

### 3.6 System Policies & Break-Glass Overrides
* **ADM-001**: Only users with `admin` or `owner` roles can adjust global data retention timelines.
* **ADM-002**: Administrators must be able to trigger a **Break-Glass Emergency Override** that bypasses standard policy checks.
* **ADM-003**: The system must require a justification input for overrides, which is stored in the audit logs.

---

## 4. Security & Privacy Controls

* **SEC-001 (Multi-Tenancy)**: Every database query, vector search, and object storage retrieval must enforce isolation by verifying the request's `tenant_id` or `organization_id`.
* **SEC-002 (Least-Privilege)**: All container services must run as rootless, non-privileged users.
* **SEC-003 (Secrets Sanitation)**: The executor must redact API keys, tokens, and passwords from logs.
* **SEC-004 (AST Analysis)**: Prior to running shell or terminal commands, the system must parse command structures to verify containment checks.

---

## 5. Performance Requirements

* **PER-001 (Latency)**: Web API routers must respond to client requests within 200ms for standard CRUD operations.
* **PER-002 (Concurrency)**: The database connection pool must recycle stale connections within 1800 seconds and prevent pool depletion during concurrent worker operations.
