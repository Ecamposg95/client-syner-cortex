# Syner Cortex - Architecture Overview

## 1. Stack Specifications
Syner Cortex is built on the **Atlas Development Framework** model:
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL/SQLite.
- **Frontend:** React 18, TypeScript, Vite, Zustand, Axios, Tailwind CSS.

## 2. Multi-Tenancy & Security Model
Every resource belongs to an `Organization` (tenant isolation).
- **Context Routing:** The frontend includes the `X-Organization-ID` header on all API calls.
- **RBAC Guardrails:** The backend dependencies decode the JWT token, lookup the user role in the target organization, and enforce allowed roles before executing business logic.
- **Roles:** `SUPERADMIN`, `SYNER_ADMIN`, `CONSULTANT`, `CLIENT_OWNER`, `CLIENT_EXECUTIVE`, `CLIENT_MANAGER`, `CLIENT_VIEWER`. Superadmins automatically bypass tenant filters to support global audits.

## 3. RAG & Vector Storage
- **Ingestion:** Documents are parsed (PDF via PyPDF2, TXT/MD natively) and split using standard overlapping chunks.
- **Embeddings:** Chunks are converted into 1536-dimensional vectors via OpenAI `text-embedding-3-small` or Gemini.
- **Offline Resilience:** If no API keys are provided in the environment, the backend falls back to generating deterministic pseudo-random unit vectors based on text hashes. This preserves full cosine similarity matching functionality offline/locally without keys!
- **Storage:** Vectors are stored as JSON arrays directly inside PostgreSQL/SQLite for ease of migration and portability.
