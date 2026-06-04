# Syner Cortex - AI Consulting Operating System

**Syner Cortex** is a multi-tenant SaaS business intelligence and AI-assisted consulting platform designed for startups, SMEs, corporate executives, and Syner consulting agents. 

The platform turns unstructured internal documentation, processes, and corporate KPIs into actionable diagnostics, cited semantic answers, and execution plans using enterprise RAG and structured decision matrices.

---

## SaaS Product Modules (18 Modules Architecture)

Syner Cortex is designed around an 18-module product catalogue, executed across four development phases:
- **Phase 1 (MVP Functional):** Cortex Core, Cortex Vault, Cortex Chat, Cortex Diagnose, Cortex Insights, Cortex Roadmap, Cortex Reports. (Implemented)
- **Phase 2 (Consulting Core):** Cortex Agents (specialized strategic agents), Cortex KPI Intelligence, Cortex Boardroom dashboard, Cortex Client Portal, Cortex Playbooks.
- **Phase 3 (Enterprise SaaS):** Cortex Benchmark, Cortex Automations, Cortex Integrations, Cortex Governance, Cortex Billing & Plans.
- **Phase 4 (Investments & Startups):** Cortex Data Room (investor reviews).

*For a detailed module-by-module breakdown and cases of use, refer to the [Full Modules Registry](file:///home/cto/Devs/syner-cortex/docs/product/modules.md).*

---

## Canonical Technology Stack

- **Backend Architecture:**
  - Python 3.12
  - FastAPI
  - SQLAlchemy 2.0 (compatible with PostgreSQL and SQLite)
  - Pydantic v2
  - python-jose (JWT auth keys)
  - PyPDF2 (document text extraction)
- **Frontend Architecture:**
  - React 18
  - TypeScript
  - Vite
  - Zustand (state management)
  - Axios (HTTP client)
  - Tailwind CSS (premium custom dark theme)
  - Lucide React (vector iconography)

---

## Directory Structure

```text
syner-cortex/
├── app/                  # FastAPI python backend
│   ├── models/           # SQLAlchemy database schemas
│   ├── schemas/          # Pydantic serialization models
│   ├── security/         # Password hashing & JWT helpers
│   ├── services/         # AI RAG & SWOT Diagnosis Engines
│   ├── routers/          # API endpoints
│   ├── database.py       # DB engine connections
│   ├── dependencies.py   # Global RBAC/JWT dependencies
│   └── main.py           # Application entrypoint
│
├── frontend/             # React Vite SPA frontend
│   ├── src/
│   │   ├── api/          # Axios HTTP client interceptors
│   │   ├── store/        # Zustand state stores
│   │   ├── components/   # Layouts & UI primitives
│   │   ├── pages/        # Auth & Dashboard pages
│   │   ├── main.tsx
│   │   └── App.tsx
│   ├── tailwind.config.js
│   └── package.json
│
├── docs/                 # Product and Architecture context
└── requirements.txt      # Python libraries
```

---

## Local Setup & Launch Guide

### 1. Install Dependencies
You can install both backend python virtualenv and frontend npm modules automatically using the root utility:
```bash
npm run install:all
```
*Note: If python-venv is missing on your host system, the script will automatically fallback to installing packages in your virtualenv by bootstrapping pip.*

### 2. Configure Environment variables
Create a `.env` file at the project root:
```env
DATABASE_URL=sqlite:///./syner_cortex.db
JWT_SECRET=super_secret_session_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Start Development Services
- **Backend FastAPI server:**
  ```bash
  .venv/bin/uvicorn app.main:app --reload
  ```
- **Frontend Vite server:**
  ```bash
  npm run dev --prefix frontend
  ```

Open your browser at [http://localhost:5173](http://localhost:5173) and log in using the pre-seeded admin user:
- **Email:** `admin@cortex.com`
- **Password:** `password123`

---

## Deployment & Builds

Syner Cortex is fully prepared for continuous deployment on **Railway** utilizing **Nixpacks**:
- Nixpacks automatically installs Python 3.12 and Node 20.
- Compiles React SPA code into production static assets.
- Runs the FastAPI web application, serving both REST API endpoints and fallback catch-all routes.
